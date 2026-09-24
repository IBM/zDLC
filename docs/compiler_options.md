---
layout: default
title: Compiler Options
nav_order: 4
---


# Compiler Options Reference

The IBM zDLC compiler is invoked via `docker run` with the `zdlc` image. This page is a complete reference for all supported options. For a quick introduction, see [Getting Started](getting_started.html).

---

## Basic invocation

```bash
docker run --rm -v <model-dir>:/workdir:z ${ZDLC_IMAGE} [OPTIONS] <model>.onnx
```

Running with no arguments or `--help` prints the full built-in help:

```bash
docker run --rm ${ZDLC_IMAGE}
```

---

## Output format options

These flags control what the compiler emits. **Exactly one must be specified.**

| Flag | Output | Use when |
|---|---|---|
| `--EmitLib` | `.so` shared library | C, C++, or Python applications |
| `--EmitJNI` | `.jar` file (JNI-wrapped `.so`) | Java applications |
| `--EmitObj` | `.o` object file | Custom linking scenarios |
| `--EmitMLIR` | MLIR intermediate representation | Debugging / inspecting lowering passes |
| `--EmitLLVMIR` | LLVM IR | Low-level debugging |
| `--EmitZHighIR` | ZHigh dialect IR | Debugging NNPA lowering |

### Example — compile to `.so` for Python or C++

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  ${ZDLC_MODEL_NAME}.onnx
```

### Example — compile to `.jar` for Java

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitJNI --O3 -march=z17 --mtriple=s390x-ibm-loz \
  ${ZDLC_MODEL_NAME}.onnx
```

---

## Target architecture options

| Flag | Description |
|---|---|
| `-march=<arch>` | Minimum CPU architecture for generated instructions. Replaces the deprecated `--mcpu` option (still supported but will be removed in a future release). |
| `--mtriple=s390x-ibm-loz` | Target triple for IBM Z Linux on Z. Required for all IBM Z compilations. |

**Common `-march` values:**

| Value | Use on |
|---|---|
| `z13` | IBM z13 and later |
| `z14` | IBM z14 and later |
| `z15` | IBM z15 and later |
| `z16` | IBM z16 and later (required for NNPA) |
| `z17` | IBM z17 and later (recommended; enables Telum II optimizations) |

> Use the highest `-march` value that matches your *deployment* hardware to get the best performance.

---

## Optimization level

| Flag | Description |
|---|---|
| `--O0` | No optimization. Useful for debugging. |
| `--O1` | Basic optimization. |
| `--O2` | Moderate optimization. |
| `--O3` | Maximum optimization. Recommended for production. |

---

## Accelerator options

| Flag | Description |
|---|---|
| `--maccel=NNPA` | Route supported ONNX operators to the IBM Z Integrated Accelerator for AI (NNPA) instead of the CPU. Requires `-march=z16` or higher. |
| `--nnpa-quant-dynamic` | Enable dynamic 8-bit integer quantization for NNPA matrix multiplications (Telum II / z17 feature). |

See [IBM Z Integrated Accelerator for AI](accelerator.html) for a full guide including device placement and performance tuning.

---

## Shape information

| Flag | Description |
|---|---|
| `--shapeInformation <spec>` | Statically fix dynamic input dimensions at compile time to allow better accelerator mapping. Format: `inputIdx:dim0xdim1x...` — use `-1` to leave a dimension dynamic. Multiple inputs are comma-separated. |

**Example** — fix height and width for a vision model with shape `(-1, -1, -1, 3)`:

```bash
--shapeInformation 0:-1x640x480x3
```

**Example** — multiple input tensors:

```bash
--shapeInformation 0:-1x640x480x3,1:-1x100
```

---

## Device placement options

| Flag | Description |
|---|---|
| `--save-config-file=<file>` | Save the default NNPA device placement decisions to a JSON file for inspection or manual editing. |
| `--config-file=<file>` | Load a device placement JSON file to override which operations target NNPA vs CPU. |

See [Device Placement](accelerator.html#device-placement) for a full walk-through with examples.

---

## Diagnostics and reporting

| Flag | Description |
|---|---|
| `--onnx-op-stats TXT` | Print a text summary of how many operators will run on CPU vs NNPA at compile time. |
| `--onnx-op-stats JSON` | Same as above but in JSON format. |
| `--opt-report=NNPAUnsupportedOps` | Print a CSV report explaining why each operator was *not* mapped to NNPA. Useful for tuning accelerator coverage. |

**Example output from `--opt-report=NNPAUnsupportedOps`:**

```
==NNPA-UNSUPPORTEDOPS-REPORT==, onnx.Mul, Mul_28, Element type is not F16 or F32.
==NNPA-UNSUPPORTEDOPS-REPORT==, onnx.Div, Div_122, Rank 0 is not supported. zAIU only supports rank in range of (0, 4].
```

---

## Debug and instrumentation options

| Flag | Description |
|---|---|
| `--enable-debug-info` | Embed DWARF debug symbols in the compiled `.so`. Enables `gdb` source-level debugging. |
| `--preserveMLIR` | Preserve MLIR intermediate files alongside the compiled output. Recommended when using `--enable-debug-info` with `.onnx` inputs. |
| `--profile-ir=<value>` | Emit runtime timing instrumentation. Values: `None` (default), `Onnx`, `ZHigh`. |
| `--instrument-stage=<value>` | Stage to instrument. Values: `Onnx`, `ZHigh`, `ZLow`. |
| `--instrument-ops=<ops>` | Comma-separated list of operations to instrument, or `onnx.*` / `zhigh.*` wildcards. |
| `--InstrumentBeforeOp` | Insert instrumentation probe before each matched operation. |
| `--InstrumentAfterOp` | Insert instrumentation probe after each matched operation. |
| `--InstrumentReportTime` | Report wall-clock time at each instrumentation point. |
| `--InstrumentReportMemory` | Report virtual memory usage at each instrumentation point. |

See [Troubleshooting and Debug](troubleshooting.html) for full examples of each option.

---

## Supported ONNX operations

| Target | Reference |
|---|---|
| CPU | [Supported ONNX Operations for CPU](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-cpu.md) |
| NNPA (IBM Z Integrated Accelerator) | [Supported ONNX Operations for NNPA](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-NNPA.md) |

Operations not listed in these tables, or usage that falls outside documented limitations, are beyond the IBM zDLC project scope.
