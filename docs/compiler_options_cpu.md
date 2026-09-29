---
layout: default
title: Compiler Options — CPU
nav_order: 4
---

# Compiler Options — CPU

This page covers all compiler flags that apply to every IBM zDLC compilation, regardless of whether you are targeting the CPU or the NNPA accelerator. For NNPA-specific flags, see [Compiler Options — NNPA](compiler_options_nnpa.html).

---

## Basic invocation

```bash
docker run --rm -v <model-dir>:/workdir:z ${ZDLC_IMAGE} [OPTIONS] <model>.onnx
```

Running with no arguments prints the full built-in help:

```bash
docker run --rm ${ZDLC_IMAGE}
```

---

## Output format

Exactly one output format flag must be specified.

| Flag | Output | Use when |
|---|---|---|
| `--EmitLib` | `.so` shared library | C, C++, or Python applications |
| `--EmitJNI` | `.jar` file (JNI-wrapped `.so`) | Java applications |
| `--EmitObj` | `.o` object file | Custom linking scenarios — *see note below* |
| `--EmitLLVMIR` | LLVM bitcode (`.bc`) | Debugging wrong model outputs — *see note below* |
| `--EmitMLIR` | MLIR IR text | *See note below* |

> **`--EmitObj` and `--EmitMLIR`:** We do not yet have concrete customer examples for these flags. If you have a use case for them, [open an issue](https://github.com/IBM/zDLC/issues) and we will document them.

> **`--EmitLLVMIR`:** Use this when your model compiles successfully but produces incorrect outputs at runtime. See [Debugging with --EmitLLVMIR](use_cases/llvmir_debugging.html) for a step-by-step walkthrough.

### Compile to `.so` for Python or C++

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  ${ZDLC_MODEL_NAME}.onnx
```

### Compile to `.jar` for Java

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitJNI --O3 -march=z17 --mtriple=s390x-ibm-loz \
  ${ZDLC_MODEL_NAME}.onnx
```

---

## Target architecture

| Flag | Description |
|---|---|
| `-march=<arch>` | Minimum CPU architecture for generated instructions. Replaces the deprecated `--mcpu` flag (still accepted, will be removed in a future release). |
| `--mtriple=s390x-ibm-loz` | Target triple for IBM Z Linux on Z. **Required for all IBM Z compilations.** |

**`-march` values:**

| Value | Minimum hardware | Notes |
|---|---|---|
| `z13` | IBM z13 | SIMD available |
| `z14` | IBM z14 | |
| `z15` | IBM z15 | |
| `z16` | IBM z16 | Minimum for NNPA |
| `z17` | IBM z17 | Recommended; enables Telum II optimizations and NNPA quantization |

> Use the highest `-march` value that matches your **deployment** hardware. Higher values allow the compiler to emit faster instructions that older hardware cannot execute.

---

## Optimization level

| Flag | Description |
|---|---|
| `--O0` | No optimization. Compile fast; useful for debugging compilation issues. |
| `--O1` | Basic optimization. |
| `--O2` | Moderate optimization. |
| `--O3` | Maximum optimization. **Recommended for production.** Enables SIMD vectorization on top of all lower-level optimizations. |

---

## Multi-threaded execution (`--parallel`)

The `--parallel` flag enables OpenMP-based multi-threaded loop execution in the compiled model. For compute-heavy models with large matrix multiplications, this can significantly improve throughput on multi-core CPU systems.

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --parallel \
  ${ZDLC_MODEL_NAME}.onnx
```

The IBM zDLC container image ships with OpenMP support built in — no extra setup is needed.

### Control thread count at runtime

After compiling with `--parallel`, set `OMP_NUM_THREADS` before running your application to control how many CPU threads the model uses:

```bash
export OMP_NUM_THREADS=8
python my_inference.py
```

If `OMP_NUM_THREADS` is not set, the runtime uses all available CPUs.

### Limit parallelization to specific operators

By default, `--parallel` parallelizes every eligible operation. Use `--parallelize-ops` to restrict it to a comma-separated list of operator types:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --parallel --parallelize-ops="onnx.MatMul,onnx.Gemm" \
  ${ZDLC_MODEL_NAME}.onnx
```

This is useful when you want parallelism only for the heaviest operations and prefer single-threaded execution elsewhere.

### See what got parallelized

Add `--opt-report=Parallel` at compile time to get a report of which operations were parallelized and which were not:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --parallel --opt-report=Parallel \
  ${ZDLC_MODEL_NAME}.onnx
```

### NNPA + parallel

When using `--parallel` with `--maccel=NNPA`, you can independently control the number of CPU threads and NNPA accelerator threads:

```bash
export OMP_NUM_THREADS=16       # CPU threads
export OM_NUM_ZAIU_THREADS=8    # NNPA accelerator threads (defaults to OMP_NUM_THREADS if unset)
python my_inference.py
```

---

## Shape information

| Flag | Description |
|---|---|
| `--shapeInformation <spec>` | Fix dynamic input dimensions at compile time. Format: `inputIdx:dim0xdim1x...` — use `-1` to leave a dimension dynamic. Multiple inputs are comma-separated. |

This is primarily useful when compiling for NNPA, where dynamic dimensions can prevent the compiler from placing operators on the accelerator. See [Dynamic Shapes](use_cases/dynamic_shapes.html) for a full walkthrough.

**Example** — fix sequence length for a BERT model with input shape `(-1, -1)`:

```bash
--shapeInformation 0:-1x128,1:-1x128
```

**Example** — fix height and width for a vision model with shape `(-1, -1, -1, 3)`:

```bash
--shapeInformation 0:-1x640x480x3
```

---

## Debug and instrumentation

| Flag | Description |
|---|---|
| `--enable-debug-info` | Embed DWARF debug symbols in the compiled `.so`. Enables `gdb` source-level debugging. |
| `--preserveMLIR` | Keep MLIR intermediate files alongside the compiled output. Recommended with `--enable-debug-info` when the input is an `.onnx` file. |
| `--profile-ir=<value>` | Emit runtime timing instrumentation. Values: `None` (default), `Onnx`, `ZHigh`. |
| `--instrument-stage=<value>` | Stage to instrument. Values: `Onnx`, `ZHigh`, `ZLow`. |
| `--instrument-ops=<ops>` | Comma-separated list of operations to instrument, or `onnx.*` / `zhigh.*` wildcards. |
| `--InstrumentBeforeOp` | Insert probe before each matched operation. |
| `--InstrumentAfterOp` | Insert probe after each matched operation. |
| `--InstrumentReportTime` | Report wall-clock time at each instrumentation point. |
| `--InstrumentReportMemory` | Report virtual memory usage at each instrumentation point. |

See [Troubleshooting and Debug](troubleshooting.html) for full examples.

---

## Supported ONNX operations

| Target | Reference |
|---|---|
| CPU | [Supported ONNX Operations for CPU](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-cpu.md) |
| NNPA | [Supported ONNX Operations for NNPA](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-NNPA.md) |

Operations not listed, or usage outside documented limitations, are beyond the IBM zDLC project scope.

---

## Flags we need your help with

The following flags exist in the compiler but we do not yet have concrete customer examples for them. If you use any of these, please [open an issue](https://github.com/IBM/zDLC/issues) so we can document them properly.

| Flag | Description |
|---|---|
| `--EmitMLIR` | Emits MLIR intermediate representation. Useful for debugging compiler lowering passes, but no end-to-end customer workflow documented yet. |
| `--EmitObj` | Emits a `.o` object file instead of a `.so`. Intended for custom linking scenarios. |
