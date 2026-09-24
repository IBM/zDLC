---
layout: default
title: Getting Started
nav_order: 2
---

# Getting Started with IBM Z Deep Learning Compiler

## Overview

The IBM Z Deep Learning Compiler (IBM zDLC) compiles `.onnx` deep learning models into shared libraries optimized for IBM Z systems. The compiled libraries integrate directly into C, C++, Java, or Python applications and automatically take advantage of IBM Z hardware including SIMD on IBM z13 and later, and the Integrated Accelerator for AI (NNPA) on IBM z16 and z17.

ONNX is an open, vendor-neutral format for representing AI models. Some frameworks (PyTorch, TensorFlow, etc.) support exporting to `.onnx` directly. For others, open source converters are available — see [ONNX Support Tools](https://onnx.ai/supported-tools.html) for a full list.

**End-to-end workflow:**
1. Obtain an ONNX model (create, convert, or download one).
2. Pull the `zdlc` container image from the IBM Z and LinuxONE Container Registry.
3. Compile the model to a shared library.
4. Import the shared library into your application.
5. Run your application.

---

## Prerequisites

- Docker installed and running on an IBM Z (s390x) system or a system with cross-compilation support.
- Access to the [IBM Z and LinuxONE Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html) (`icr.io`).

---

## Step 1 — Pull the IBM zDLC container image

Credentials for `icr.io` are required. See [IBM Z and LinuxONE Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html) for access instructions.

Set the image version you want to use:

```bash
ZDLC_IMAGE=icr.io/ibmz/zdlc:5.1.0
```

Pull the image:

```bash
docker pull ${ZDLC_IMAGE}
```

---

## Step 2 — Clone the examples repository

```bash
git clone https://github.com/IBM/zDLC
ZDLC_DIR=$(pwd)/zDLC
```

---

## Step 3 — Set environment variables

These variables are used throughout all examples. Set them once in your shell session.

```bash
GCC_IMAGE_ID=icr.io/ibmz/gcc:15.2
JDK_IMAGE_ID=icr.io/ibmz/openjdk:21-jammy
ZDLC_CODE_DIR=${ZDLC_DIR}/code
ZDLC_LIB_DIR=${ZDLC_DIR}/lib
ZDLC_BUILD_DIR=${ZDLC_DIR}/build
ZDLC_MODEL_DIR=${ZDLC_DIR}/models
ZDLC_MODEL_NAME=mnist-12
if [ -z ${ZDLC_IMAGE} ]; then echo ERROR: ZDLC_IMAGE must be set first; fi
if [ -z ${ZDLC_DIR} ] || [ ! -d ${ZDLC_DIR} ]; then echo ERROR: ZDLC_DIR must be set to an existing zDLC directory first; fi
```

| Variable | Purpose |
|---|---|
| `ZDLC_IMAGE` | The zDLC compiler container image and version. |
| `ZDLC_DIR` | Root of the cloned example repository. |
| `GCC_IMAGE_ID` | GCC container used to compile and run C++ examples. |
| `JDK_IMAGE_ID` | OpenJDK container used to compile and run Java examples. |
| `ZDLC_CODE_DIR` | Directory containing example source code. |
| `ZDLC_LIB_DIR` | Directory where the PyRuntime library will be extracted. |
| `ZDLC_BUILD_DIR` | Directory for C++/Java build artifacts and runtime headers. |
| `ZDLC_MODEL_DIR` | Directory containing `.onnx` model files. |
| `ZDLC_MODEL_NAME` | Model name without file extension (e.g. `mnist-12`). |

---

## Step 4 — Obtain a model

Download the MNIST example model from the ONNX Model Zoo:

```bash
wget --directory-prefix $ZDLC_MODEL_DIR \
  https://github.com/onnx/models/raw/main/validated/vision/classification/mnist/model/${ZDLC_MODEL_NAME}.onnx
```

Or browse [Verified ONNX Models](https://github.com/IBM/zDLC/blob/main/models/README.md) for the full list of verified models, or [ONNX Support Tools](https://onnx.ai/supported-tools.html) for converters from other frameworks.

---

## Step 5 — Compile the model

Use `--EmitLib` to compile the `.onnx` file into a `.so` shared library:

```bash
docker run --rm \
  -v ${ZDLC_MODEL_DIR}:/workdir:z \
  ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  ${ZDLC_MODEL_NAME}.onnx
```

| Flag | Description |
|---|---|
| `--EmitLib` | Output a `.so` shared library. |
| `--O3` | Highest optimization level. |
| `-march=z17` | Target CPU architecture. Use `z16` for z16 systems. |
| `--mtriple=s390x-ibm-loz` | Target triple for IBM Z Linux. |

The compiled `.so` is written to `${ZDLC_MODEL_DIR}`.

> For a full description of all compiler flags, see [Compiler Options](compiler_options.html).  
> To target the Integrated Accelerator for AI, see [IBM Z Integrated Accelerator for AI](accelerator.html).

---

## Step 6 — Run your application

Choose the language that fits your application:

| Language | Next step |
|---|---|
| **Python** | Continue below for the generic Python example, or see [Encoder LLM](use_cases/encoder_llm.html) / [Credit Card Fraud Detection](use_cases/credit_card_fraud.html) for full end-to-end examples. |
| **C++** | See [C++ and Java Inference](use_cases/cpp_java.html) for the full build and run walkthrough. |
| **Java** | See [C++ and Java Inference](use_cases/cpp_java.html) for the full build and run walkthrough. |

---

## Running the generic Python example

The generic Python example runs inference on any compiled `.so` using the ONNX-MLIR [PyRuntime](http://onnx.ai/onnx-mlir/UsingPyRuntime.html).

First, extract the PyRuntime library from the container:

```bash
mkdir -p ${ZDLC_LIB_DIR}
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/files:z \
  --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} \
  -c "cp /usr/local/lib/PyRuntime* /files"
```

Build the Python example container:

```bash
docker build \
  -f ${ZDLC_DIR}/docker/Dockerfile.python \
  -t zdlc-python-example .
```

Run inference:

```bash
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/build/lib:z \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  --env PYTHONPATH=/build/lib \
  zdlc-python-example:latest \
  /code/deep_learning_compiler_run_model_python.py \
  /models/${ZDLC_MODEL_NAME}.so
```

Expected output (values will be random since the input is random):

```
The input tensor dimensions are:
[1, 3, 224, 224]
A brief overview of the output tensor is:
[[-2.4883294   0.4591511   1.1298141  ... -2.8113475  -1.3842212
   2.6721394 ]
 [-5.064701    0.17290297 -1.866698   ...  0.39307398 -4.6048536
   2.116905  ]]
The dimensions of the output tensor are:
(3, 1000)
```

Source code: [`code/deep_learning_compiler_run_model_python.py`](https://github.com/IBM/zDLC/blob/main/code/deep_learning_compiler_run_model_python.py)

---

## Verify the compiler CLI

Running the image with no arguments prints the full compiler help:

```bash
docker run --rm ${ZDLC_IMAGE}
```

Or with `--help` for the same output.
