# Use Case: LLM Inference with Triton Inference Server

This guide shows how to serve IBM zDLC-compiled models using the [IBM Z Accelerated for NVIDIA Triton™ Inference Server](https://github.com/IBM/ibmz-accelerated-for-nvidia-triton-inference-server), enabling HTTP/gRPC-based inference suitable for production deployments.

**What you'll build:** A Triton Inference Server instance running on IBM Z serving a zDLC-compiled BERT model via REST API, with both a "use the provided model" path and a "bring your own model" path.

**Prerequisites:** Complete [Getting Started](../getting_started.md) and the [Encoder LLM](encoder_llm.md) example first — you need a compiled `model.so` before proceeding.

---

## Overview

[Triton Inference Server](https://docs.nvidia.com/deeplearning/triton-inference-server/archives/triton-inference-server-2410/user-guide/docs/user_guide/architecture.html) is an open-source, high-performance AI inference server. The IBM Z variant adds an **ONNX-MLIR backend** that loads IBM zDLC-compiled `.so` model libraries directly, giving you:

- HTTP (port 8000) and gRPC (port 8001) inference endpoints
- Dynamic batching and multi-model serving
- A metrics endpoint (port 8002) for monitoring
- REST APIs for model management and health checks

---

## Step 1 — Pull the Triton container image

```bash
TRITON_IMAGE=icr.io/ibmz/ibmz-accelerated-for-nvidia-triton-inference-server:X.Y.Z
docker pull ${TRITON_IMAGE}
```

Replace `X.Y.Z` with the version available in the [IBM Z and LinuxONE Container Registry](https://ibm.github.io/ibm-z-oss-hub/containers/ibmz-accelerated-for-nvidia-triton-inference-server.html).

---

## Step 2 — Compile your model with IBM zDLC

If you already have a compiled `model.so` from the [Encoder LLM](encoder_llm.md) example, skip this step.

To compile `bert-large-uncased` with NNPA acceleration:

```bash
docker run --rm \
  -v ${ZDLC_MODEL_DIR}:/workdir:z \
  ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  bert-large-uncased/bert-large-uncased.onnx
```

> **Bring your own model:** Export any ONNX-compatible model using your framework's export tools, then compile it with the command above. The Triton ONNX-MLIR backend will load any IBM zDLC-compiled `.so` file — no Triton-specific changes to the model are required.

---

## Step 3 — Create the Triton model repository

Triton requires a specific directory layout. Create it from your compiled `.so`:

```bash
MODEL_REPO=${ZDLC_DIR}/triton_models
MODEL_NAME=bert-large-uncased

mkdir -p ${MODEL_REPO}/${MODEL_NAME}/1
cp ${ZDLC_MODEL_DIR}/${MODEL_NAME}/${MODEL_NAME}.so ${MODEL_REPO}/${MODEL_NAME}/1/model.so
```

Create the model configuration file `config.pbtxt`:

```bash
cat > ${MODEL_REPO}/${MODEL_NAME}/config.pbtxt << 'EOF'
backend: "onnxmlir"
max_batch_size: 32

input [
  {
    name: "input_ids"
    data_type: TYPE_INT64
    dims: [ 128 ]
  },
  {
    name: "attention_mask"
    data_type: TYPE_INT64
    dims: [ 128 ]
  },
  {
    name: "token_type_ids"
    data_type: TYPE_INT64
    dims: [ 128 ]
  }
]

output [
  {
    name: "last_hidden_state"
    data_type: TYPE_FP32
    dims: [ 128, 1024 ]
  }
]
EOF
```

> **Important:** The `input` and `output` names and dimensions must match the actual tensor names and shapes in your compiled model. Run `docker run --rm ${ZDLC_IMAGE} --printIR ${MODEL_NAME}.onnx` to inspect them, or refer to the Hugging Face model card.

The final model repository layout:

```
triton_models/
└── bert-large-uncased/
    ├── 1/
    │   └── model.so
    └── config.pbtxt
```

---

## Step 4 — Launch Triton Inference Server

```bash
docker run --shm-size 1G --rm \
  -p 8000:8000 \
  -p 8001:8001 \
  -p 8002:8002 \
  -v ${MODEL_REPO}:/models \
  ${TRITON_IMAGE} \
  tritonserver --model-repository=/models
```

| Port | Service |
|---|---|
| 8000 | HTTP inference endpoint |
| 8001 | gRPC inference endpoint |
| 8002 | Prometheus metrics |

Verify the server is ready:

```bash
curl -v localhost:8000/v2/health/ready
```

A `200 OK` response means the server is ready. A non-200 response means it is still loading or has encountered an error — check the container logs.

---

## Step 5 — Send an inference request

Use `curl` to send a REST inference request:

```bash
curl -X POST localhost:8000/v2/models/${MODEL_NAME}/infer \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": [
      {
        "name": "input_ids",
        "shape": [1, 128],
        "datatype": "INT64",
        "data": [101, 2073, 2003, 3000, 1029, 102, 0, 0, ...]
      },
      {
        "name": "attention_mask",
        "shape": [1, 128],
        "datatype": "INT64",
        "data": [1, 1, 1, 1, 1, 1, 0, 0, ...]
      },
      {
        "name": "token_type_ids",
        "shape": [1, 128],
        "datatype": "INT64",
        "data": [0, 0, 0, 0, 0, 0, 0, 0, ...]
      }
    ]
  }'
```

---

## Model management REST APIs

| Operation | Endpoint |
|---|---|
| List models | `POST v2/repository/index` |
| Load a model | `POST v2/repository/models/{model_name}/load` |
| Unload a model | `POST v2/repository/models/{model_name}/unload` |
| Get model config | `GET v2/models/{model_name}/config` |
| Server health | `GET v2/health/ready` |

---

## Supported backends

The IBM Z Triton image ships four backends:

| Backend | `backend` value in `config.pbtxt` | Use for |
|---|---|---|
| ONNX-MLIR | `"onnxmlir"` | IBM zDLC-compiled `.so` models |
| Python | `"python"` | Custom Python inference logic, pre/post-processing |
| PyTorch | `"pytorch"` | PyTorch models via IBM Z Accelerated for PyTorch |
| Snap ML C++ | `"ibmsnapml"` | Scikit-learn, XGBoost, LightGBM tree ensembles |

For full backend documentation see the [IBM Z Accelerated for NVIDIA Triton™ Inference Server repository](https://github.com/IBM/ibmz-accelerated-for-nvidia-triton-inference-server).

---

## What's coming

- End-to-end LLM serving example with tokenization pre-processing pipeline
- Decoder model serving (GPT-2, T5)
- Triton Model Analyzer integration for throughput/latency tuning

See [Decoder LLM Inference](decoder_llm.md) for the decoder roadmap.
