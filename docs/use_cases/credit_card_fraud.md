---
layout: default
title: Credit Card Fraud Detection
parent: Use Cases
nav_order: 2
---


# Use Case: Credit Card Fraud Detection

This guide walks through a complete end-to-end example: training a fraud detection model in PyTorch, exporting it to ONNX, compiling it with IBM zDLC, and running accelerated inference on IBM Z.

**What you'll build:** A Python or C++ application that scores financial transactions against a trained fraud detection model, compiled to run on the IBM Z Integrated Accelerator for AI (NNPA).

**Prerequisites:** Complete [Getting Started](../getting_started.html) first and have your environment variables set, including `GCC_IMAGE_ID` if you want to run the C++ example. You will also need the [Credit Card Fraud dataset](https://github.com/IBM/TabFormer/tree/main/data/credit_card).

---

## Step 1 — Set environment variables

```bash
ZDLC_CODE_DIR=${ZDLC_DIR}/code/credit_card_fraud_example
ZDLC_LIB_DIR=${ZDLC_DIR}/lib
ZDLC_BUILD_DIR=${ZDLC_DIR}/build
ZDLC_MODEL_DIR=${ZDLC_DIR}/models
ZDLC_DATA_DIR=${ZDLC_DIR}/data
ZDLC_MODEL_NAME=ccfd
```

---

## Step 2 — Prepare the dataset

Download the [Credit Card Fraud dataset](https://github.com/IBM/TabFormer/tree/main/data/credit_card) (`transactions.tgz`) and extract it:

```bash
mkdir -p ${ZDLC_DATA_DIR}
tar -xvzf /path/to/transactions.tgz -C ${ZDLC_DATA_DIR}
```

> **Bring your own model:** If you already have a trained fraud detection model exported as `.onnx`, skip Steps 3 and 4 and go directly to Step 5. Place your `.onnx` file at `${ZDLC_MODEL_DIR}/${ZDLC_MODEL_NAME}.onnx`.

---

## Step 3 — Build the training container

```bash
docker build \
  -f ${ZDLC_DIR}/docker/Dockerfile.ccfd_train \
  -t ccfd-pytorch-train-example:latest .
```

---

## Step 4 — Train the model and export to ONNX

```bash
docker run --rm \
  -v ${ZDLC_DATA_DIR}:/data:z \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  --userns=keep-id --user $(id -u):$(id -g) \
  ccfd-pytorch-train-example:latest \
  /code/credit_card_fraud_training.py
```

`--userns=keep-id --user $(id -u):$(id -g)` runs the container as your host user, so the `ccfd.onnx` it writes to the bind-mounted `${ZDLC_MODEL_DIR}` is owned by you.

Training iterates over multiple epochs — the epoch number in the output shows progress. When complete, `ccfd.onnx` is written to `${ZDLC_MODEL_DIR}`.

---

## Step 5 — Compile the model with IBM zDLC

```bash
docker run --rm \
  -v ${ZDLC_MODEL_DIR}:/workdir:z \
  ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  ${ZDLC_MODEL_NAME}.onnx
```

The compiled `ccfd.so` is written to `${ZDLC_MODEL_DIR}`.

See [Compiler Options — CPU](../compiler_options_cpu.html) for a full flag reference and [Compiler Options — NNPA](../compiler_options_nnpa.html) for NNPA tuning guidance.

---

## Step 6 — Run inference

Run the compiled `ccfd.so` from either Python or C++. Both use the same model and the same random `[1, 7, 220]` input shape. Choose one.

> The input is randomly generated for this example. In production, replace it with real transaction data. Output values near `1.0` indicate a high fraud probability. Because the inputs are random, the output value changes between runs and differs between the Python and C++ examples.

### Option A — Python

Extract the PyRuntime library from the container:

```bash
mkdir -p ${ZDLC_LIB_DIR}
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/files:z \
  --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} \
  -c "cp /usr/local/lib/PyRuntime* /files"
```

Build the inference container:

```bash
docker build \
  -f ${ZDLC_DIR}/docker/Dockerfile.python \
  -t zdlc-python-ccfd-example:latest .
```

Run inference:

```bash
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/build/lib:z \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  --env PYTHONPATH=/build/lib \
  zdlc-python-ccfd-example:latest \
  code/credit_card_fraud_inference.py /models/${ZDLC_MODEL_NAME}.so
```

Expected output:

```
Input Tensor has shape (1, 7, 220) and values:
[[[0.20302147 0.56236434 0.13909294 ... 0.10022413 0.9104976  0.9770127 ]
  ...]]
Output Tensor has shape (1, 1) and values:
[[0.9999949]]
```

### Option B — C++

This uses the generic C++ example, which reads the model's input signature at run time and fills the input with random values, so it works with `ccfd.so` unchanged. See [Python, C++ and Java Inference](cpp_java_python.html) for a description of the build flags.

Copy the ONNX-MLIR runtime headers and libraries out of the container:

```bash
mkdir -p ${ZDLC_BUILD_DIR}
docker run --rm \
  -v ${ZDLC_BUILD_DIR}:/files:z \
  --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} \
  -c "cp -r /usr/local/{include,lib} /files"
```

Pull the GCC container:

```bash
docker pull ${GCC_IMAGE_ID}
```

Compile the program against `ccfd.so`. The source is in `${ZDLC_DIR}/code`, not in the fraud example directory, so it is mounted separately. The executable is written next to `ccfd.so` so that `-Wl,-rpath='$ORIGIN'` can find the model at run time:

```bash
docker run --rm \
  -v ${ZDLC_DIR}/code:/code:z \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  -v ${ZDLC_BUILD_DIR}:/build:z \
  ${GCC_IMAGE_ID} \
  g++ -std=c++11 -O3 \
  -I /build/include \
  /code/deep_learning_compiler_run_model_example.cpp \
  -l:${ZDLC_MODEL_NAME}.so -L/models \
  -Wl,-rpath='$ORIGIN' \
  -o /models/ccfd_cpp_example
```

Run it:

```bash
docker run --rm \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  ${GCC_IMAGE_ID} \
  /models/ccfd_cpp_example
```

Expected output:

```
output_tensor[0] has shape [ 1 1 ] and values of type float[]:
	0.182861
```

---

## Source code

| File | Description |
|---|---|
| [`code/credit_card_fraud_example/credit_card_fraud_training.py`](https://github.com/IBM/zDLC/blob/main/code/credit_card_fraud_example/credit_card_fraud_training.py) | Trains the fraud detection model and exports it to ONNX. |
| [`code/credit_card_fraud_example/credit_card_fraud_inference.py`](https://github.com/IBM/zDLC/blob/main/code/credit_card_fraud_example/credit_card_fraud_inference.py) | Runs inference using the compiled `.so` model. |
| [`code/credit_card_fraud_example/credit_card_fraud_data_utils.py`](https://github.com/IBM/zDLC/blob/main/code/credit_card_fraud_example/credit_card_fraud_data_utils.py) | Data loading and preprocessing utilities. |
| [`code/deep_learning_compiler_run_model_example.cpp`](https://github.com/IBM/zDLC/blob/main/code/deep_learning_compiler_run_model_example.cpp) | Generic C++ program that runs inference using the compiled `.so` model. |
| [`docker/Dockerfile.ccfd_train`](https://github.com/IBM/zDLC/blob/main/docker/Dockerfile.ccfd_train) | Container environment for training. |
| [`docker/Dockerfile.python`](https://github.com/IBM/zDLC/blob/main/docker/Dockerfile.python) | Container environment for Python inference. |
