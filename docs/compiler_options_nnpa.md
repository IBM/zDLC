---
layout: default
title: Compiler Options — NNPA
nav_order: 5
---

# Compiler Options — NNPA

IBM z16 and z17 systems include an Integrated Accelerator for AI (NNPA — Neural Network Processing Assist) built into the Telum processor. This page covers all flags for enabling, tuning, and debugging NNPA acceleration. For flags that apply to every compilation (output format, optimization level, parallelism), see [Compiler Options — CPU](compiler_options_cpu.html).

> **Hardware note:** Any IBM Z system can *compile* a model targeting NNPA. Models compiled with NNPA enabled will only *run* on z16 or z17 systems. CPU-compiled models run everywhere.

---

## Enabling NNPA

Add `--maccel=NNPA` along with `-march=z16` or `-march=z17`:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  ${ZDLC_MODEL_NAME}.onnx
```

The compiler automatically:
- Routes supported operators to NNPA.
- Keeps unsupported operators on the CPU.
- Handles all required data format conversions between CPU and NNPA.

No changes are required to your model or application code.

---

## Controlling which operators go to NNPA

### `--nnpa-placement-heuristic`

By default the compiler places every operator that *qualifies* for NNPA onto the accelerator. The `--nnpa-placement-heuristic` flag raises the bar so that only operators that are *measurably faster* on NNPA are placed there.

| Value | Behavior |
|---|---|
| `QualifyingOps` | **(default)** Place every operator that qualifies for NNPA. |
| `FasterOps` | Place only operators that are estimated to be faster on NNPA than CPU. |
| `FasterOpsWSU` | Same as `FasterOps`, but also accounts for the stick/unstick format conversion overhead. |
| `MuchFasterOpsWSU` | Same as `FasterOpsWSU`, but requires a larger estimated speedup margin. |

The `stick/unstick` cost matters because each operator that crosses the CPU↔NNPA boundary incurs a format conversion (NNPA uses a tiled DLFloat16 layout). For models where many operators alternate rapidly between CPU and NNPA, `FasterOpsWSU` or `MuchFasterOpsWSU` can actually improve end-to-end latency by keeping more operators together on the CPU.

**Example — use conservative placement:**

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --nnpa-placement-heuristic=FasterOpsWSU \
  ${ZDLC_MODEL_NAME}.onnx
```

**Workflow tip:** Start with the default `QualifyingOps`. If performance is not better than CPU-only, switch to `FasterOpsWSU` and re-measure.

---

## Diagnosing operator placement

### See how many operators are on NNPA vs CPU

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --onnx-op-stats TXT \
  ${ZDLC_MODEL_NAME}.onnx
```

Use `--onnx-op-stats JSON` for machine-readable output.

> **Automatic warning:** The compiler automatically prints a warning at compile time if any of the nine compute-heavy operator types (`Conv`, `Gemm`, `GRU`, `LSTM`, `MatMul`, `MatMulInteger`, `QLinearMatMul`, `RNN`, `Softmax`) end up on CPU instead of NNPA. No extra flag is needed — look for lines like:
> ```
> [Warning] There are 2 onnx.Conv, 1 onnx.MatMul operations that run on CPU (not accelerated by NNPA).
> ```

### Understand why an operator missed NNPA

`--opt-report=NNPAUnsupportedOps` prints a CSV explaining each operator that was not mapped to NNPA:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitZHighIR --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --opt-report=NNPAUnsupportedOps \
  ${ZDLC_MODEL_NAME}.onnx
```

Sample output:
```
==NNPA-UNSUPPORTEDOPS-REPORT==, onnx.Mul, Mul_28, Element type is not F16 or F32.
==NNPA-UNSUPPORTEDOPS-REPORT==, onnx.Div, Div_122, Rank 0 is not supported. zAIU only supports rank in range of (0, 4].
```

Common reasons an operator stays on CPU:
- Data type is not F16 or F32.
- Tensor rank is outside `(0, 4]`.
- The operation is not supported by NNPA — see [Supported ONNX Operations for NNPA](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-NNPA.md).

### Inspect NNPA placement in the IR

The `--EmitZHighIR` and `--EmitZLowIR` flags stop compilation early and print the intermediate representation, letting you see exactly which operators went to NNPA and which stayed on CPU.

| Flag | What you see |
|---|---|
| `--EmitZHighIR` | After ONNX→NNPA lowering. `zhigh.*` ops = NNPA. `onnx.*` ops = CPU. |
| `--EmitZLowIR` | After ZHigh→hardware lowering. Shows the low-level NNPA instruction calls. |

**Example — check placement for BERT:**

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitZHighIR --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  bert-base-uncased.onnx 2>&1 | grep -E "(onnx\.|zhigh\.)" | head -40
```

In the output:
- Lines with `zhigh.MatMul`, `zhigh.Softmax`, `zhigh.LSTM`, etc. are running on NNPA.
- Lines with `onnx.MatMul`, `onnx.Softmax`, etc. are running on CPU.

If an operator you expected on NNPA shows up as `onnx.*`, pair this with `--opt-report=NNPAUnsupportedOps` to find out why.

---

## Dynamic input shapes and NNPA

Models with dynamic dimensions (`-1` in the input signature) may have operators that the compiler cannot safely assign to NNPA. This is because the compiler needs to verify hardware constraints (like maximum tensor sizes) at compile time, but without a concrete value it cannot do the check — so it conservatively falls back to CPU.

**Fix with `--shapeInformation`:** Provide concrete values for dynamic dimensions at compile time so the compiler can verify NNPA constraints and place more operators on the accelerator.

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --shapeInformation 0:-1x128,1:-1x128 \
  bert-base-uncased.onnx
```

**Escape hatch — `--nnpa-disable-shape-restriction`:** Skip the compile-time constraint checks entirely and trust that runtime values will be within NNPA's limits. Use with caution — if a runtime tensor violates the hardware limits, the model will fail at runtime rather than at compile time.

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --nnpa-disable-shape-restriction \
  ${ZDLC_MODEL_NAME}.onnx
```

See [Dynamic Shapes](use_cases/dynamic_shapes.html) for a full step-by-step walkthrough with BERT.

---

## Quantization (z17 / Telum II only)

IBM Telum II (z17) supports 8-bit signed-integer quantized matrix multiplications on NNPA. For transformer-based models, this can significantly improve throughput with minimal accuracy impact.

**Enable dynamic quantization:**

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --nnpa-quant-dynamic \
  ${ZDLC_MODEL_NAME}.onnx
```

`--nnpa-quant-dynamic` requires `-march=z17`. It has no effect on z16.

**Optional — control symmetric vs asymmetric quantization:**

```bash
--nnpa-quant-dynamic=symWeight,symActivation
```

Accepted values (comma-separated): `symWeight`, `asymWeight`, `symActivation`, `asymActivation`. When given with no value, the compiler chooses automatically.

**Accuracy note:** Quantizing all eligible matmuls at once sometimes degrades accuracy. If you see accuracy regression, use the JSON config file to selectively disable quantization for specific operators. See [JSON Configuration File](use_cases/json_config.html).

> For complete scale/zero-point math and worked examples, see the [ONNX-MLIR Quantization documentation](https://github.com/onnx/onnx-mlir/blob/main/docs/Quantization-NNPA.md).

> **Stale flag warning:** Older scripts may use `--nnpa-quantization=DynSymI8`. This flag no longer exists. The current equivalent is `--nnpa-quant-dynamic=symWeight,symActivation`.

---

## Device placement with a JSON config file

The `--save-config-file` and `--config-file` flags let you inspect and manually override which individual operations run on NNPA versus the CPU. This is useful for fine-grained control that the placement heuristic alone cannot provide.

### Step 1 — Save the default placement decisions

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --save-config-file=${ZDLC_MODEL_NAME}.json \
  ${ZDLC_MODEL_NAME}.onnx
```

This writes `<model>.json` to your model directory with the placement decision for every operation.

### Step 2 — Edit the JSON

Open the file and change `"device": "nnpa"` to `"device": "cpu"` (or vice versa) for any node you want to override:

```json
{
  "nnpa_ops_config": [
    {
      "pattern": {
        "match": {
          "node_type": "onnx.Gemm",
          "onnx_node_name": "Plus214-Times212_2"
        },
        "rewrite": {
          "device": "cpu"
        }
      }
    }
  ]
}
```

### Step 3 — Compile with the modified file

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --config-file=${ZDLC_MODEL_NAME}.json \
  ${ZDLC_MODEL_NAME}.onnx
```

> **Note:** Specifying `"device": "nnpa"` in the JSON is a *request*, not a guarantee. The compiler still enforces hardware constraints (type, rank, tensor size). An op explicitly routed to NNPA that fails a legality check will still fall back to CPU.

See [JSON Configuration File](use_cases/json_config.html) for a full guide including selective quantization via `nnpa_ops_config`.

For the complete JSON schema, see the [ONNX-MLIR JSON config documentation](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/JsonConfigFile-NNPA.md).

---

## Supported ONNX operations for NNPA

See [Supported ONNX Operations for NNPA](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-NNPA.md) for the complete list of operators and any operation-specific limitations.

---

## Flags we need your help with

The following NNPA flags exist in the compiler but we do not yet have concrete customer examples for them. If you use any of these, please [open an issue](https://github.com/IBM/zDLC/issues).

| Flag | Notes |
|---|---|
| `--nnpa-cpu-dql` | Routes `DynamicQuantizeLinear` computation to CPU. Activated by graph structure, not command line — relevant if your model was pre-quantized externally. |
| `--nnpa-cpu-dql-scale` | Narrower variant: computes only scale/zero-point on CPU. Same activation pattern as above. |
| `--nnpa-disable-hugepage-malloc` | Disables huge-page memory allocation for NNPA buffers. No customer example found. |
| `--nnpa-quant-op-types` | Restricts which op types get quantized (e.g. `MatMul,Conv`). Must be paired with `--nnpa-quant-dynamic` — has no effect alone. |
