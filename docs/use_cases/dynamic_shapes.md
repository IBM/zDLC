---
layout: default
title: Dynamic Shapes
parent: Use Cases
nav_order: 5
---

# Dynamic Shapes and NNPA Acceleration

Many ONNX models exported from PyTorch or HuggingFace have *dynamic* input dimensions — dimensions shown as `-1` or `?` that vary from call to call (e.g. variable batch size or sequence length). This guide explains what that means for NNPA placement and how to get the best out of the accelerator.

---

## What "dynamic" means at compile time

A dynamic dimension is one the compiler does not know at compile time. For example, a BERT model exported with a variable sequence length has an input shape like:

```
input_ids:      [batch_size, sequence_length]   →   [-1, -1]
attention_mask: [batch_size, sequence_length]   →   [-1, -1]
```

At **runtime**, every tensor always has a concrete shape — NNPA hardware only ever sees actual numbers. The "dynamic" label is purely a compile-time concept meaning *"we don't know this value yet."*

---

## Why dynamic shapes can hurt NNPA coverage

Before placing an operator on NNPA, the compiler must verify that the runtime tensor sizes will satisfy the hardware's constraints — for example, convolution kernels must be at most 64 pixels wide, and tensors must have rank in the range `(0, 4]`.

When a dimension is dynamic, the compiler has no value to check against. Rather than risk a runtime failure, it conservatively keeps the operator on CPU.

**The result:** a model that could run 80%+ on NNPA ends up running mostly on CPU because the compiler could not prove safety at compile time.

---

## Step-by-step: BERT with dynamic sequence length

### Step 1 — Compile with dynamic shapes (naive)

```bash
export ZDLC_IMAGE=icr.io/ibmz/zdlc:5.1.0
export ZDLC_MODEL_DIR=$(pwd)/models
export ZDLC_MODEL_NAME=bert-base-uncased

docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  ${ZDLC_MODEL_NAME}.onnx
```

You will likely see a warning like:

```
[Warning] There are 12 onnx.MatMul operations that run on CPU (not accelerated by NNPA).
```

### Step 2 — Inspect placement with `--EmitZHighIR`

To see exactly which operators went to NNPA and which stayed on CPU, stop compilation at the ZHigh dialect stage:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitZHighIR --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  ${ZDLC_MODEL_NAME}.onnx 2>&1 | grep -E "^[[:space:]]*(onnx|zhigh)\."
```

In the output:
- `zhigh.MatMul`, `zhigh.Softmax`, `zhigh.LSTM`, etc. → running on **NNPA**
- `onnx.MatMul`, `onnx.Softmax`, etc. → running on **CPU**

If your key compute operators (MatMul, Softmax) show as `onnx.*`, that confirms the dynamic shape issue.

### Step 3 — Fix with `--shapeInformation`

Tell the compiler the concrete sequence length you will use at runtime. For BERT with `batch_size=1, sequence_length=128`:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  --shapeInformation 0:-1x128,1:-1x128 \
  ${ZDLC_MODEL_NAME}.onnx
```

The format is `inputIndex:dim0xdim1x...`. Use `-1` to leave a dimension truly dynamic; use a positive integer to fix it. Here we fix sequence length to 128 but leave batch size dynamic.

After this compile, the warning should be gone and `--EmitZHighIR` should show your MatMul and Softmax operations as `zhigh.*`.

> **Note:** The compiled model is now optimized for sequence length 128. If you run it with a different sequence length at runtime, it will still work — NNPA always receives concrete values — but the compiler's optimization decisions were made for 128. For best performance, compile once for each sequence length you care about.

### Step 4 — Validate the improvement

After recompiling with `--shapeInformation`, compare `--onnx-op-stats` before and after:

```bash
# Without shapeInformation
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --onnx-op-stats TXT \
  ${ZDLC_MODEL_NAME}.onnx

# With shapeInformation
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --onnx-op-stats TXT \
  --shapeInformation 0:-1x128,1:-1x128 \
  ${ZDLC_MODEL_NAME}.onnx
```

You should see the count of `zhigh.*` operators increase and `onnx.*` operators decrease.

---

## Escape hatch: `--nnpa-disable-shape-restriction`

If you want to force NNPA placement even when the compiler cannot verify constraints, use `--nnpa-disable-shape-restriction`:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --nnpa-disable-shape-restriction \
  ${ZDLC_MODEL_NAME}.onnx
```

This tells the compiler: *"trust me, the values that arrive at runtime will satisfy NNPA's constraints."*

> **Warning:** If that trust is violated at runtime — for example, a convolution kernel that is wider than NNPA supports — the model will fail at runtime rather than at compile time. Use `--shapeInformation` when possible; use `--nnpa-disable-shape-restriction` only when you are confident about the runtime ranges.

---

## Reference

| Flag | Purpose |
|---|---|
| `--shapeInformation 0:dim0xdim1x...` | Fix dynamic dimensions at compile time |
| `--nnpa-disable-shape-restriction` | Skip compile-time constraint checks (use with care) |
| `--EmitZHighIR` | Inspect which operators are on NNPA vs CPU |
| `--opt-report=NNPAUnsupportedOps` | Get a per-operator explanation of why ops missed NNPA |
| `--onnx-op-stats TXT` | Count of operators on NNPA vs CPU |

See [Compiler Options — NNPA](../compiler_options_nnpa.html) for full flag descriptions.
