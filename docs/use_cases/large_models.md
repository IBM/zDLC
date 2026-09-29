---
layout: default
title: Large Models (External Data)
parent: Use Cases
nav_order: 6
---

# Compiling Large Models with External Data

ONNX models that contain large weights (typically above 2 GB) cannot be stored as a single `.onnx` file due to the protobuf format's 2 GB size limit. Instead, the model weights are split into a separate binary file — a format ONNX calls *external data*. This guide walks through converting a large model to external data format and compiling it with IBM zDLC.

---

## What external data means

A standard `.onnx` file contains both the model graph (operators and their connections) and all the model weights (tensors) in a single binary protobuf file. For large models like LLaMA, GPT, or large BERT variants, the weights alone can exceed several gigabytes.

External data format splits this into two files:
- `model.onnx` — the graph structure (small)
- `model.onnx.data` — the weight tensors (large)

The IBM zDLC compiler handles both files together. You mount the directory and point the compiler at the `.onnx` file; it automatically locates the accompanying data file.

---

## Step 1 — Export your model to external data format

Use the `onnx` Python library to save the model with external data. This step happens **before** you invoke the zDLC compiler.

```python
import onnx

# Load the model (must already be in ONNX format)
model = onnx.load("my_large_model.onnx")

# Save with external data
# The weights will be written to my_large_model.onnx.data
onnx.save_model(
    model,
    "my_large_model.onnx",
    save_as_external_data=True,
    all_tensors_to_one_file=True,
    location="my_large_model.onnx.data",
    size_threshold=1024,   # tensors larger than 1 KB go to external file
    convert_attribute=False,
)
```

After this, your model directory should contain:

```
models/
├── my_large_model.onnx         ← graph structure
└── my_large_model.onnx.data    ← all weight tensors
```

### Exporting from HuggingFace with Optimum

If you are exporting a HuggingFace model, use the `optimum` CLI, which handles external data automatically for large models:

```bash
pip install optimum[exporters]

optimum-cli export onnx \
  --model meta-llama/Llama-2-7b-hf \
  --task text-generation-with-past \
  --framework pt \
  ./llama2-7b-onnx/
```

The exported directory will already contain the `.onnx` + external data files if the model is large enough.

---

## Step 2 — Compile with IBM zDLC

Mount the entire model directory into the container. The compiler reads both the `.onnx` and the data file from the same directory:

```bash
export ZDLC_IMAGE=icr.io/ibmz/zdlc:5.1.0
export ZDLC_MODEL_DIR=$(pwd)/models

docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA \
  my_large_model.onnx
```

The output `my_large_model.so` is written to the same directory.

### With NNPA quantization (z17 only)

For very large transformer models, dynamic quantization can significantly reduce memory footprint and improve throughput:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --nnpa-quant-dynamic \
  my_large_model.onnx
```

---

## Step 3 — Run inference

The compiled `.so` is self-contained — it does not reference the external data file at runtime. All weights are embedded in or linked to the shared library during compilation.

```python
import numpy as np
import onnxruntime as rt  # or use the zDLC Python runtime

# Load the compiled library
# (Using the zDLC Python runtime — see Getting Started for setup)
import sys
sys.path.append("/path/to/zdlc/runtime/python")
from PyRuntime import OMExecutionSession

session = OMExecutionSession("./my_large_model.so")

# Run inference
input_ids = np.array([[101, 2054, 2003, 1996, 3081, 102]], dtype=np.int64)
outputs = session.run(input_ids)
```

---

## Troubleshooting

### Out of memory during compilation

Large model compilation can require significant RAM. If the Docker container runs out of memory:

1. Increase Docker's memory limit in Docker Desktop settings.
2. If compiling on a resource-constrained system, consider using `--O2` instead of `--O3` to reduce compiler memory usage.

### "Cannot find external data file"

Ensure the `.onnx` and `.data` files are in the **same directory** that you mount with `-v`. The compiler resolves the data file path relative to the `.onnx` file's location.

### Model accuracy with quantization

Quantizing all matmuls at once sometimes degrades accuracy for large models. See [JSON Configuration File](json_config.html) for how to selectively disable quantization for specific operators.

---

## Reference

| Concept | Notes |
|---|---|
| External data export | `onnx.save_model(..., save_as_external_data=True)` — Python preprocessing step |
| HuggingFace export | `optimum-cli export onnx` — handles external data automatically |
| Compile command | Same as any other model — mount the directory, point at `.onnx` |
| Runtime | Compiled `.so` is self-contained; no `.data` file needed at runtime |
