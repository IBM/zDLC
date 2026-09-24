---
layout: default
title: IBM Z Integrated Accelerator for AI
nav_order: 5
---


# IBM Z Integrated Accelerator for AI (NNPA)

IBM z16 and z17 systems include an Integrated Accelerator for AI (also called NNPA — Neural Network Processing Assist) built into the Telum processor. IBM zDLC can automatically route supported ONNX operations to this accelerator, giving you real-time AI inference at transaction scale with no changes to your model.

> **Hardware note:** Any IBM Z system can *compile* a model targeting NNPA. However, models compiled with NNPA enabled will only *run* on systems that have the accelerator (z16 and later). Systems with the accelerator can run CPU-compiled models, but those models will not use the accelerator.

---

## Enabling NNPA acceleration

Add `--maccel=NNPA` to your compile command. Because the accelerator requires z16 or later hardware, also set `-march=z16` or `-march=z17`:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  ${ZDLC_MODEL_NAME}.onnx
```

The compiler automatically handles:
- Routing supported operators to NNPA.
- Keeping unsupported operators on the CPU.
- Any required data format conversions between CPU and NNPA.

No changes are required to your model or your application code.

---

## NNPA quantization (z17 / Telum II)

IBM Telum II (z17) supports 8-bit signed-integer quantized matrix multiplications on NNPA, which can significantly improve throughput for transformer-based models.

Add `--nnpa-quant-dynamic` to let the compiler automatically choose quantization options:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --nnpa-quant-dynamic \
  ${ZDLC_MODEL_NAME}.onnx
```

For full quantization options see [ONNX-MLIR NNPA Quantization Overview](https://github.com/onnx/onnx-mlir/blob/main/docs/Quantization-NNPA.md).

---

## Performance tuning

### Fix dynamic input dimensions

Models with dynamic dimensions (shown as `-1` in the input signature) may have operators that the compiler cannot safely assign to NNPA at compile time. Fixing those dimensions with `--shapeInformation` allows the compiler to map more operations to the accelerator.

**Example** — vision model with input shape `(-1, -1, -1, 3)`:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --shapeInformation 0:-1x640x480x3 \
  ${ZDLC_MODEL_NAME}.onnx
```

Use `-1` to leave a dimension dynamic and a specific integer to fix it. Multiple input tensors are comma-separated:

```bash
--shapeInformation 0:-1x640x480x3,1:-1x100
```

### View operator placement at compile time

Use `--onnx-op-stats` to see a summary of how many operators will run on CPU vs NNPA:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --onnx-op-stats TXT \
  ${ZDLC_MODEL_NAME}.onnx
```

Operations prefixed with `onnx.*` run on CPU; operations prefixed with `zhigh.*` run on NNPA.

Pair this with `--shapeInformation` to iterate until you are satisfied with the NNPA coverage.

### Understand why operators missed NNPA

`--opt-report=NNPAUnsupportedOps` prints a CSV explaining each operator that was *not* mapped to NNPA:

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
- Tensor rank is outside the range `(0, 4]`.
- The operation is simply not supported by NNPA (see [Supported ONNX Operations for NNPA](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-NNPA.md)).

---

## Device placement <a id="device-placement"></a>

Device placement lets you inspect and manually override which operations run on NNPA versus the CPU. This is an advanced option useful when you need fine-grained control over accelerator usage.

> Note: Specifying NNPA as a target does not *guarantee* that operation runs on NNPA — the compiler still enforces hardware constraints (type, rank, tensor size, and operator support).

### Step 1 — Save the default placement to a JSON file

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --save-config-file=${ZDLC_MODEL_NAME}.json \
  ${ZDLC_MODEL_NAME}.onnx
```

This writes `<model>.json` to `${ZDLC_MODEL_DIR}` with the placement decisions for every operation.

### Step 2 — Edit the JSON to change a target

Open the JSON and change `"device": "nnpa"` to `"device": "cpu"` (or vice versa) for any operation node you want to override.

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

### Step 3 — Compile with the modified placement file

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --config-file=${ZDLC_MODEL_NAME}.json \
  ${ZDLC_MODEL_NAME}.onnx
```

For full JSON schema documentation see the [open source device placement documentation](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/JsonConfigFile-NNPA.md).

---

## Supported ONNX operations for NNPA

See [Supported ONNX Operations for IBM Z Integrated Accelerator (NNPA)](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-NNPA.md) for the complete list of operators and any operation-specific limitations.
