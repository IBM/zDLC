# Getting Started with IBM Z Deep Learning Compiler

## Overview

The IBM Z Deep Learning Compiler (IBM zDLC) compiles `.onnx` deep learning models into shared libraries optimized for IBM Z systems. The compiled libraries integrate directly into C, C++, Java, or Python applications and automatically take advantage of IBM Z hardware including SIMD on IBM z13 and later, and the Integrated Accelerator for AI (NNPA) on IBM z16 and z17.

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

Or browse [models/README.md](../models/README.md) for the full list of verified models, or [ONNX Support Tools](https://onnx.ai/supported-tools.html) for converters from other frameworks.

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

> For a full description of all compiler flags, see [Compiler Options](compiler_options.md).  
> To target the Integrated Accelerator for AI, see [IBM Z Integrated Accelerator for AI](accelerator.md).

---

## Step 6 — Run your application

Choose the language that fits your application:

| Language | Next step |
|---|---|
| **Python** | [Encoder LLM use case](use_cases/encoder_llm.md) or [Credit Card Fraud Detection](use_cases/credit_card_fraud.md) for end-to-end Python examples. |
| **C++** | See the [C++ runtime API](../code/deep_learning_compiler_run_model_example.cpp) and refer to the compiler options page for `--EmitLib` build flags. |
| **Java** | See the [Java runtime API](../code/deep_learning_compiler_run_model_example.java) and build with `--EmitJNI`. |

---

## Verify the compiler CLI

Running the image with no arguments prints the full compiler help:

```bash
docker run --rm ${ZDLC_IMAGE}
```

Or with `--help` for the same output.
