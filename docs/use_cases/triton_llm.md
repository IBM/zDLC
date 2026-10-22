---
layout: default
title: LLM Serving with Triton
parent: Use Cases
nav_order: 4
---


# Use Case: LLM Inference with Triton Inference Server

This guide shows how to serve IBM zDLC-compiled models using the [IBM Z Accelerated for NVIDIA Triton™ Inference Server](https://github.com/IBM/ibmz-accelerated-for-nvidia-triton-inference-server), enabling HTTP/gRPC-based inference suitable for production deployments.

**What you'll build:** A Triton Inference Server instance running on IBM Z serving a zDLC-compiled BERT model via REST API, with both a "use the provided model" path and a "bring your own model" path.

**Prerequisites:** Complete [Getting Started](../getting_started.html) (Steps 1–3) and Steps 1–4 of the [Encoder LLM](bert_base.html) example first. You need the exported `bert-large-uncased.onnx` and a compiled `bert-large-uncased.so` in `${ZDLC_MODEL_DIR}/bert-large-uncased/` before proceeding. The Encoder LLM example's remaining steps (PyRuntime extraction and Python inference) are not required.

---

## Overview

[Triton Inference Server](https://docs.nvidia.com/deeplearning/triton-inference-server/archives/triton-inference-server-2410/user-guide/docs/user_guide/architecture.html) is an open-source, high-performance AI inference server. The IBM Z variant adds an **ONNX-MLIR backend** that loads IBM zDLC-compiled `.so` model libraries directly, giving you:

- HTTP (port 8000) and gRPC (port 8001) inference endpoints
- Dynamic batching and multi-model serving
- A metrics endpoint (port 8002) for monitoring
- REST APIs for model management and health checks

---

## Step 1 — Set variables and pull the Triton container image

This page uses `ZDLC_IMAGE`, `ZDLC_DIR` and `ZDLC_MODEL_DIR` from [Getting Started](../getting_started.html) and the [Encoder LLM](bert_base.html) example. Variables set in one shell session are not available in another, so set them again if you open a new session. Then add the two Triton variables:

```bash
TRITON_IMAGE=icr.io/ibmz/ibmz-accelerated-for-nvidia-triton-inference-server:X.Y.Z
MODEL_NAME=bert-large-uncased
MODEL_REPO=${ZDLC_DIR}/triton_models
docker pull ${TRITON_IMAGE}
```

Replace `X.Y.Z` with the version available in the [IBM Z and LinuxONE Container Registry](https://ibm.github.io/ibm-z-oss-hub/containers/ibmz-accelerated-for-nvidia-triton-inference-server.html).

---

## Step 2 — Compile your model with IBM zDLC

If you already compiled `bert-large-uncased` in Step 4 of the [Encoder LLM](bert_base.html) example, skip this step.

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

Create the model configuration file `config.pbtxt`. The Encoder LLM example exports `bert-large-uncased` with the default `MLM` task, which produces a `logits` output over the 30,522-token vocabulary. The model has a dynamic sequence length, and this configuration fixes it at 128 tokens:

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
    name: "logits"
    data_type: TYPE_FP32
    dims: [ 128, 30522 ]
  }
]
EOF
```

> **Important:** The `input` and `output` names and dimensions must match the tensors in your compiled model. If you exported a different task (for example `EMBED`, whose output is `last_hidden_state`) or a different model, list the real names and shapes from the `.onnx` file and update the configuration:
>
> ```bash
> docker run --rm --entrypoint python3 -v ${ZDLC_MODEL_DIR}:/models:z zdlc-llm-example:latest -c "
> import onnx
> m = onnx.load('/models/${MODEL_NAME}/${MODEL_NAME}.onnx', load_external_data=False)
> for t in list(m.graph.input) + list(m.graph.output):
>     print(t.name, [d.dim_value or d.dim_param for d in t.type.tensor_type.shape.dim])"
> ```

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

Triton runs in the foreground. Open a second terminal on the same host (and set the variables again) to run the commands below. Verify the server is ready:

```bash
curl -v http://127.0.0.1:8000/v2/health/ready
```

A `200 OK` response means the server is ready. A non-200 response means it is still loading or has encountered an error — check the container logs.

> **Tip:** Use `127.0.0.1` rather than `localhost`. With rootless Podman, `localhost` can resolve to the IPv6 address `::1`, where the forwarded port resets the connection (`curl: (56) Recv failure: Connection reset by peer`).

---

## Step 5 — Send an inference request

The model expects tokenized input padded to 128 tokens, so generate the request body with the tokenizer saved in Step 3 of the Encoder LLM example. This writes `request.json` and prints the position of the `[MASK]` token:

```bash
docker run --rm --user $(id -u):$(id -g) --userns=keep-id --entrypoint python3 \
  -v ${ZDLC_MODEL_DIR}:/models:z zdlc-llm-example:latest -c "
import json
from transformers import BertTokenizer
t = BertTokenizer.from_pretrained('/models/${MODEL_NAME}')
e = t('The capital of [MASK] is Paris.', padding='max_length', max_length=128, truncation=True, return_tensors='np')
inputs = [{'name': k, 'shape': [1, 128], 'datatype': 'INT64', 'data': e[k].flatten().tolist()}
          for k in ['input_ids', 'attention_mask', 'token_type_ids']]
json.dump({'inputs': inputs}, open('/models/request.json', 'w'))
print('mask position:', e['input_ids'][0].tolist().index(t.mask_token_id))"
```

Send the request with `curl`. The response contains 128 × 30,522 values (about 40 MB), so write it to a file:

```bash
curl -s -X POST http://127.0.0.1:8000/v2/models/${MODEL_NAME}/infer \
  -H "Content-Type: application/json" \
  -d @${ZDLC_MODEL_DIR}/request.json \
  -o ${ZDLC_MODEL_DIR}/response.json
head -c 200 ${ZDLC_MODEL_DIR}/response.json
```

The response begins with `{"model_name":"bert-large-uncased",...,"outputs":[{"name":"logits","datatype":"FP32","shape":[1,128,30522],...`.

To confirm the output is meaningful, decode the highest-scoring token at the mask position. Set `m` to the mask position printed above (4 for the sentence shown):

```bash
docker run --rm --entrypoint python3 -v ${ZDLC_MODEL_DIR}:/models:z zdlc-llm-example:latest -c "
import json
from transformers import BertTokenizer
t = BertTokenizer.from_pretrained('/models/${MODEL_NAME}')
d = json.load(open('/models/response.json'))['outputs'][0]['data']
v, m = 30522, 4
row = d[m * v:(m + 1) * v]
print('predicted:', t.convert_ids_to_tokens(max(range(v), key=row.__getitem__)))"
```

For this sentence the predicted token is `france`.

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
