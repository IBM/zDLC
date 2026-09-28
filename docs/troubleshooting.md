---
layout: default
title: Troubleshooting and Debug
nav_order: 6
---


# Troubleshooting and Debug

IBM zDLC provides several compile-time options that embed diagnostic information into compiled models. This page covers all debug and instrumentation options with examples.

> **Performance note:** All instrumentation options add overhead to model runtime. Use them during development and testing, not in production.

---

## Debug symbols (`--enable-debug-info`)

The `--enable-debug-info` flag embeds DWARF debug symbols in the compiled `.so`, enabling source-level debugging with tools like `gdb`.

When compiling from an `.onnx` file, also add `--preserveMLIR` to keep the MLIR intermediate representation files — this gives debuggers additional context:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --enable-debug-info --preserveMLIR \
  ${ZDLC_MODEL_NAME}.onnx
```

| Flag | Effect |
|---|---|
| `--enable-debug-info` | Adds symbol tables, line numbers, and metadata to the `.so`. Increases file size. |
| `--preserveMLIR` | Keeps MLIR intermediate files alongside the output for enhanced debug context. |

For more on using debug info in testing see [ONNX-MLIR Testing documentation](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/Testing.md).

---

## Profile IR (`--profile-ir`)

`--profile-ir` inserts lightweight timing probes around each operation and prints elapsed time to stdout when the model runs. It is the quickest way to find which operations are taking the most time.

| Value | What is profiled |
|---|---|
| `None` | No profiling (default). |
| `Onnx` | All ONNX-level operations. |
| `ZHigh` | NNPA zhigh-level operations. |

Use `--profile-ir=<value>` or `--profile-ir-with-sig=<value>` — both accept the same values. The `-with-sig` variant additionally prints tensor signatures (shapes and types) at each probe point.

### Example — profile ONNX ops

Compile:
```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --profile-ir=Onnx \
  ${ZDLC_MODEL_NAME}.onnx
```

Sample runtime output:
```
#0) before onnx.Constant Time elapsed: 1692618036.154512 accumulated: 1692618036.154512 (Times212_reshape1)
#1) after  onnx.Constant Time elapsed: 0.000005 accumulated: 1692618036.154517 (Times212_reshape1)
```

### Example — profile ZHigh (NNPA) ops

Compile:
```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --profile-ir=ZHigh \
  ${ZDLC_MODEL_NAME}.onnx
```

Sample runtime output:
```
#10) before zhigh.Conv2D Time elapsed: 0.000003 accumulated: 1692617935.010779 (...)
#11) after  zhigh.Conv2D Time elapsed: 0.000161 accumulated: 1692617935.010940 (...)
```

> ⚠️ **Required:** You must call `OMInstrumentInit` in your application **before** loading the model shared library. If this call is missing, all instrumentation output is silently suppressed — no error will be shown.

---

## Instrument options (`--instrument-stage`, `--instrument-ops`)

The instrument options give finer-grained control over what is profiled compared to `--profile-ir`. You choose the lowering stage, the specific operations, and what to report.

### Choose a stage (`--instrument-stage`)

| Value | What is profiled |
|---|---|
| `Onnx` | ONNX-level ops. When `--maccel=NNPA` is also set, profiles before lowering to ZHigh. |
| `ZHigh` | Both ONNX and ZHigh (NNPA) ops. |
| `ZLow` | ZLow (low-level NNPA) ops. |

### Choose operations (`--instrument-ops`)

| Value | Matches |
|---|---|
| `NONE` or `""` | Nothing (disables instrumentation). |
| `onnx.Conv,onnx.Add` | Specific named operations. |
| `onnx.*` | All ONNX operations (wildcard). |
| `zhigh.*` | All ZHigh operations (wildcard). |
| `onnx.*,zhigh.*` | All ONNX and ZHigh operations. |

### Choose what to report

| Flag | Reports |
|---|---|
| `--InstrumentBeforeOp` | Probe fires before each matched operation. |
| `--InstrumentAfterOp` | Probe fires after each matched operation. |
| `--InstrumentReportTime` | Wall-clock time at each probe point. |
| `--InstrumentReportMemory` | Virtual memory (VMem) at each probe point. |

### Example — time ONNX ops before NNPA lowering

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz --maccel=NNPA \
  --instrument-stage=Onnx --instrument-ops=onnx.* \
  --InstrumentBeforeOp --InstrumentAfterOp --InstrumentReportTime \
  ${ZDLC_MODEL_NAME}.onnx
```

Sample output:
```
#  0) before onnx.Constant Time elapsed: 1691688479.493696 accumulated: 1691688479.493696
#  1) after  onnx.Constant Time elapsed: 0.000005 accumulated: 1691688479.493701
```

### Example — time both ONNX and ZHigh ops

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz --maccel=NNPA \
  --instrument-stage=ZHigh --instrument-ops=onnx.*,zhigh.* \
  --InstrumentBeforeOp --InstrumentAfterOp --InstrumentReportTime \
  ${ZDLC_MODEL_NAME}.onnx
```

Sample output:
```
# 24) before onnx.Reshape  Time elapsed: 0.000002 accumulated: 1691688806.270982
# 25) after  onnx.Reshape  Time elapsed: 0.000001 accumulated: 1691688806.270983
# 26) before zhigh.Stick   Time elapsed: 0.000002 accumulated: 1691688806.270985
# 27) after  zhigh.Stick   Time elapsed: 0.000003 accumulated: 1691688806.270988
```

### Example — memory profiling for ZLow ops

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz --maccel=NNPA \
  --instrument-stage=ZLow --instrument-ops=zlow.* \
  --InstrumentBeforeOp --InstrumentAfterOp --InstrumentReportMemory \
  ${ZDLC_MODEL_NAME}.onnx
```

Sample output:
```
# 14) before zlow.matmul VMem:  5456
# 15) after  zlow.matmul VMem:  5456
# 16) before zlow.add    VMem:  5456
# 17) after  zlow.add    VMem:  5456
```

---

## NNPA unsupported ops report (`--opt-report=NNPAUnsupportedOps`)

This report tells you exactly *why* each operation was not placed on NNPA. Run it when you want to understand or improve your model's accelerator coverage.

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitZHighIR --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --opt-report=NNPAUnsupportedOps \
  ${ZDLC_MODEL_NAME}.onnx
```

Output format: `==NNPA-UNSUPPORTEDOPS-REPORT==, <op>, <node name>, <reason>`

```
==NNPA-UNSUPPORTEDOPS-REPORT==, onnx.Mul, Mul_28, Element type is not F16 or F32.
==NNPA-UNSUPPORTEDOPS-REPORT==, onnx.Div, Div_122, Rank 0 is not supported. zAIU only supports rank in range of (0, 4].
```

---

## Removing the IBM zDLC container image

Find the image ID:
```bash
docker images
```

Remove it:
```bash
docker rmi <IMAGE-ID>
```

If a container is still running, stop and remove it first:
```bash
docker ps -a
docker stop <CONTAINER-ID>
docker rm <CONTAINER-ID>
docker rmi <IMAGE-ID>
```
