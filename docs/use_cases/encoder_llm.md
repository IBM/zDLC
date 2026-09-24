---
layout: default
title: Encoder LLM Inference (BERT)
parent: Use Cases
nav_order: 1
---


# Use Case: Encoder LLM Inference (BERT)

This guide walks through compiling and running encoder-based LLM inference on IBM Z using IBM zDLC. The example uses BERT but applies to any encoder-based transformer architecture.

**What you'll build:** A Python application that runs BERT inference accelerated by the IBM Z Integrated Accelerator for AI (NNPA), covering four use cases: Masked Language Modeling, Semantic Similarity, Embeddings, and Question Answering.

**Prerequisites:** Complete [Getting Started](../getting_started.html) first and have your environment variables set.

---

## Supported use cases

| Use case | Flag | What it does |
|---|---|---|
| Masked Language Modeling | `--task MLM` | Predicts a masked word in a sentence. |
| Embeddings | `--task EMBED` | Produces contextual vector embeddings for a sentence. |
| Semantic Similarity | `--task SS` | Scores how semantically similar two sentences are. |
| Question Answering | `--task QNA` | Extracts an answer from a passage given a question. |
| Text Summarization | `--task SUMMARIZE` | Extracts key information from longer documents and generates a concise summary. |

---

## Step 1 — Set environment variables

```bash
ZDLC_CODE_DIR=${ZDLC_DIR}/code/LLM
ZDLC_LIB_DIR=${ZDLC_DIR}/lib
ZDLC_MODEL_DIR=${ZDLC_DIR}/models
ZDLC_MODEL_NAME=bert-large-uncased
ZDLC_MODEL_TASK=MLM
```

---

## Step 2 — Build the LLM example container

This container includes Python and the required libraries to download a BERT model from Hugging Face and convert it to ONNX format. It uses the IBM Z Accelerated for PyTorch image as its base.

```bash
docker build \
  --build-arg UID=$(id -u) \
  --build-arg GID=$(id -g) \
  -f ${ZDLC_DIR}/docker/Dockerfile.llm \
  -t zdlc-llm-example .
```

| Flag | Description |
|---|---|
| `--build-arg UID=$(id -u)` | Sets the container user ID to match the host user, avoiding file permission issues on bind mounts. |
| `--build-arg GID=$(id -g)` | Sets the container group ID to match the host group. |
| `-f docker/Dockerfile.llm` | Dockerfile for the LLM example environment. |
| `-t zdlc-llm-example` | Tag for the built image. |

---

## Step 3 — Download and convert the BERT model

The `download_bert_model.py` script downloads a BERT model from Hugging Face and exports it to ONNX format.

```bash
docker run --rm \
  --user $(id -u):$(id -g) --userns=keep-id \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  zdlc-llm-example:latest \
  /code/download_bert_model.py \
  --model-type ${ZDLC_MODEL_TASK} \
  --model-name ${ZDLC_MODEL_NAME}
```

Run `/code/download_bert_model.py --help` for a full list of supported models and tasks.

> **Bring your own model:** Replace `--model-name` with any BERT-compatible model name from [Hugging Face](https://huggingface.co/models). The script handles the ONNX export. For non-BERT architectures, export to ONNX manually using your framework's export tooling and skip to Step 4.

---

## Step 4 — Compile the model with IBM zDLC

Compile the ONNX model to a `.so` shared library targeting the NNPA accelerator:

```bash
docker run --rm \
  -v ${ZDLC_MODEL_DIR}:/workdir:z \
  ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  ${ZDLC_MODEL_NAME}/${ZDLC_MODEL_NAME}.onnx
```

### Optional: enable dynamic quantization (z17 only)

On IBM z17 (Telum II), NNPA supports 8-bit integer quantized matrix multiplications. Add `--nnpa-quant-dynamic` for improved throughput on transformer models:

```bash
docker run --rm \
  -v ${ZDLC_MODEL_DIR}:/workdir:z \
  ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --nnpa-quant-dynamic \
  ${ZDLC_MODEL_NAME}/${ZDLC_MODEL_NAME}.onnx
```

See [Compiler Options](../compiler_options.html) for a full flag reference and [IBM Z Integrated Accelerator for AI](../accelerator.html) for NNPA tuning guidance.

---

## Step 5 — Extract the PyRuntime library

```bash
mkdir -p ${ZDLC_LIB_DIR}
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/files:z \
  --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} \
  -c "cp /usr/local/lib/PyRuntime* /files"
```

---

## Step 6 — Run inference

### Masked Language Modeling

Predict the masked word in a sentence:

```bash
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/build/lib:z \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  --env PYTHONPATH=/build/lib \
  zdlc-llm-example:latest \
  /code/llm_example.py \
  --task MLM \
  --text-one "The capital of [MASK] is Paris" \
  --model bert-large-uncased
```

### Embeddings

Generate a contextual embedding vector for a sentence:

```bash
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/build/lib:z \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  --env PYTHONPATH=/build/lib \
  zdlc-llm-example:latest \
  /code/llm_example.py \
  --task EMBED \
  --text-one "Where is Paris?" \
  --model bert-base-uncased
```

### Semantic Similarity

Score how similar two sentences are:

```bash
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/build/lib:z \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  --env PYTHONPATH=/build/lib \
  zdlc-llm-example:latest \
  /code/llm_example.py \
  --task SS \
  --text-one "Where is Paris?" \
  --text-two "Where is France?" \
  --model bert-large-uncased
```

### Question Answering

Extract an answer from a passage. Requires a QNA fine-tuned model:

```bash
docker run --rm \
  -v ${ZDLC_LIB_DIR}:/build/lib:z \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_MODEL_DIR}:/models:z \
  --env PYTHONPATH=/build/lib \
  zdlc-llm-example:latest \
  /code/llm_example.py \
  --task QNA \
  --text-one "What country is Paris in?" \
  --text-two "Paris is known for love, art, and fashion. Paris is located in France." \
  --model deepset/bert-base-uncased-squad2
```

> **Note:** QNA requires downloading a question-answering fine-tuned model. Pass the Hugging Face model name to `download_bert_model.py --model-name deepset/bert-base-uncased-squad2 --model-type QNA` first.

---

## Source code

| File | Description |
|---|---|
| [`code/LLM/download_bert_model.py`](https://github.com/IBM/zDLC/blob/main/code/LLM/download_bert_model.py) | Downloads and converts BERT models from Hugging Face to ONNX. |
| [`code/LLM/llm_example.py`](https://github.com/IBM/zDLC/blob/main/code/LLM/llm_example.py) | Runs inference for MLM, EMBED, SS, and QNA tasks. |
| [`docker/Dockerfile.llm`](https://github.com/IBM/zDLC/blob/main/docker/Dockerfile.llm) | Container environment for the LLM examples. |
