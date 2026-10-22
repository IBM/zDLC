---
layout: default
title: Debugging with --EmitLLVMIR
parent: Use Cases
nav_order: 7
---

# Debugging with `--EmitLLVMIR`

`--EmitLLVMIR` stops compilation at the LLVM IR stage and emits a `.bc` bitcode file instead of a compiled `.so`. This is your primary tool when a model **compiles successfully but produces incorrect outputs at runtime**.

---

## When to use this

Use `--EmitLLVMIR` when:

- The model compiles without errors but inference results are wrong (NaN, garbage values, or consistently incorrect predictions).
- You want to verify that a specific optimization or lowering step is not introducing a numerical error.
- You are preparing a bug report for the IBM zDLC team and need to provide a reproducible intermediate artifact.

Do **not** use this as a first debugging step for compilation failures (where `--EmitZHighIR` is more useful) or for NNPA placement questions (use `--EmitZHighIR` + `--opt-report=NNPAUnsupportedOps`).

---

## Step 1 — Emit LLVM bitcode

Replace `--EmitLib` with `--EmitLLVMIR`:

```bash
export ZDLC_IMAGE=icr.io/ibmz/zdlc:5.1.0
export ZDLC_MODEL_DIR=$(pwd)/models
export ZDLC_MODEL_NAME=my_model

docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLLVMIR --O3 -march=z17 --mtriple=s390x-ibm-loz \
  ${ZDLC_MODEL_NAME}.onnx
```

This produces `my_model.bc` in your model directory instead of `my_model.so`.

---

## Step 2 — Disassemble to human-readable IR

`.bc` files are binary. Use `llvm-dis` to convert to readable text:

```bash
# Run llvm-dis inside the zDLC container (it ships the matching LLVM toolchain)
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z \
  --entrypoint llvm-dis ${ZDLC_IMAGE} \
  /workdir/${ZDLC_MODEL_NAME}.bc -o /workdir/${ZDLC_MODEL_NAME}.ll
```

This writes `my_model.ll` — the human-readable LLVM IR — to your model directory.

---

## Step 3 — Inspect the IR

Open `my_model.ll` in any text editor. Things to look for:

**Unexpected constant folding or constant values:**
```
; Check initializer tensors look reasonable
; Large sections of `zeroinitializer` where you expect real weights
; are a sign weights were not loaded correctly.
```

**NaN-producing operations:**
```llvm
; Look for divisions where the denominator could be zero
%div = fdiv float %a, %b
; or sqrt of negative values
%sqrt = call float @llvm.sqrt.f32(float %val)
```

**Type mismatches:**
```llvm
; Unexpected integer ops where you expect float ops
; or i8/i16 where you expect f32
```

**Comparison with a known-good compile:**
If you have a CPU-compiled version that works correctly, emit LLVM IR for both and compare:

```bash
# CPU-only compile
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLLVMIR --O3 -march=z17 --mtriple=s390x-ibm-loz \
  my_model.onnx

mv ${ZDLC_MODEL_DIR}/my_model.ll ${ZDLC_MODEL_DIR}/my_model_cpu.ll

# NNPA compile
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLLVMIR --O3 -march=z17 --mtriple=s390x-ibm-loz --maccel=NNPA \
  my_model.onnx

mv ${ZDLC_MODEL_DIR}/my_model.ll ${ZDLC_MODEL_DIR}/my_model_nnpa.ll

diff my_model_cpu.ll my_model_nnpa.ll
```

---

## Step 4 — Bisect with lower optimization levels

If you find a suspicious pattern in the IR, narrow it down by reducing the optimization level:

```bash
# Try O0 (no optimization) to see if the issue is in the optimizer
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLLVMIR --O0 -march=z17 --mtriple=s390x-ibm-loz \
  ${ZDLC_MODEL_NAME}.onnx
```

If `--O0` produces correct results but `--O3` does not, there is an optimization-level-dependent bug — include this information in your bug report.

---

## Filing a bug report

When opening a GitHub issue for a wrong-output bug, include:

1. The model name and source (HuggingFace model ID, ONNX Model Zoo entry, or your own model).
2. The full compile command (with all flags).
3. The `my_model.ll` file (or a relevant excerpt — search for the function containing the suspicious operation).
4. A minimal Python script that reproduces the wrong output.
5. What output you expected vs what you got (values, not just "it's wrong").

[Open an issue on GitHub →](https://github.com/IBM/zDLC/issues)

---

## Reference

| Flag | Purpose |
|---|---|
| `--EmitLLVMIR` | Stop at LLVM IR stage, emit `.bc` bitcode file |
| `--EmitZHighIR` | Stop at ZHigh dialect (NNPA placement debugging) |
| `--EmitMLIR` | Stop at MLIR stage (no customer example yet — [open an issue](https://github.com/IBM/zDLC/issues) if you need this) |

See [Compiler Options — CPU](../compiler_options_cpu.html) for the full output format reference.
