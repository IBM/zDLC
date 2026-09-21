# Use Case: Credit Card Fraud Detection

This guide walks through a complete end-to-end example: training a fraud detection model in PyTorch, exporting it to ONNX, compiling it with IBM zDLC, and running accelerated inference on IBM Z.

**What you'll build:** A Python application that scores financial transactions against a trained fraud detection model, compiled to run on the IBM Z Integrated Accelerator for AI (NNPA).

**Prerequisites:** Complete [Getting Started](../getting_started.md) first and have your environment variables set. You will also need the [Credit Card Fraud dataset](https://github.com/IBM/TabFormer/tree/main/data/credit_card).

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
  ccfd-pytorch-train-example:latest \
  /code/credit_card_fraud_training.py
```

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

See [Compiler Options](../compiler_options.md) for a full flag reference and [IBM Z Integrated Accelerator for AI](../accelerator.md) for NNPA tuning guidance.

---

## Step 6 — Extract the PyRuntime library

```bash
mkdir -p ${ZDLC_LIB_DIR}
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/files:z \
  --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} \
  -c "cp /usr/local/lib/PyRuntime* /files"
```

---

## Step 7 — Build the inference container

```bash
docker build \
  -f ${ZDLC_DIR}/docker/Dockerfile.python \
  -t zdlc-python-ccfd-example:latest .
```

---

## Step 8 — Run inference

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

> The input is randomly generated for this example. In production, replace it with real transaction data. Output values near `1.0` indicate a high fraud probability.

---

## Source code

| File | Description |
|---|---|
| [`code/credit_card_fraud_example/credit_card_fraud_training.py`](../../code/credit_card_fraud_example/credit_card_fraud_training.py) | Trains the fraud detection model and exports it to ONNX. |
| [`code/credit_card_fraud_example/credit_card_fraud_inference.py`](../../code/credit_card_fraud_example/credit_card_fraud_inference.py) | Runs inference using the compiled `.so` model. |
| [`code/credit_card_fraud_example/credit_card_fraud_data_utils.py`](../../code/credit_card_fraud_example/credit_card_fraud_data_utils.py) | Data loading and preprocessing utilities. |
| [`docker/Dockerfile.ccfd_train`](../../docker/Dockerfile.ccfd_train) | Container environment for training. |
| [`docker/Dockerfile.python`](../../docker/Dockerfile.python) | Container environment for Python inference. |
