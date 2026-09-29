---
layout: default
title: Home
nav_order: 1
---

# IBM Z Deep Learning Compiler (IBM zDLC)

The IBM Z Deep Learning Compiler compiles `.onnx` AI models into optimized shared libraries for IBM Z systems. Compiled models run in C, C++, Java, or Python applications and automatically take advantage of IBM Z hardware — including SIMD on IBM z13 and later, and the Integrated Accelerator for AI (NNPA) on IBM z16 and z17.

IBM zDLC is built on [ONNX-MLIR](http://onnx.ai/onnx-mlir/) and is distributed as a container image from the [IBM Z and LinuxONE Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).

---

## Documentation

### Getting started

| Page | Description |
|---|---|
| [Getting Started](docs/getting_started.html) | Install, set up environment variables, compile your first model, and pick a language runtime. |

### Use cases

| Page | Description |
|---|---|
| [Encoder LLM Inference (BERT)](docs/use_cases/encoder_llm.html) | End-to-end BERT inference with NNPA acceleration — MLM, embeddings, semantic similarity, and QA. |
| [LLM Serving with Triton Inference Server](docs/use_cases/triton_llm.html) | Serve zDLC-compiled models via HTTP/gRPC using the IBM Z Triton Inference Server. |
| [Credit Card Fraud Detection](docs/use_cases/credit_card_fraud.html) | Train a PyTorch model, compile it with zDLC, and run accelerated fraud scoring on IBM Z. |
| [C++ and Java Inference](docs/use_cases/cpp_java.html) | Build and run C++ and Java applications against zDLC-compiled models. |
| [Dynamic Shapes](docs/use_cases/dynamic_shapes.html) | Get maximum NNPA coverage for models with variable-length inputs like BERT. |
| [Large Models (External Data)](docs/use_cases/large_models.html) | Compile models over 2 GB by splitting weights to an external data file first. |
| [JSON Configuration File](docs/use_cases/json_config.html) | Store compile flags and control per-operator NNPA placement and quantization in a versioned JSON file. |
| [Debugging with --EmitLLVMIR](docs/use_cases/llvmir_debugging.html) | Diagnose wrong model outputs using LLVM IR inspection. |
| [Decoder LLM Inference](docs/use_cases/decoder_llm.html) | *(Coming soon)* GPT-2 and T5 decoder inference examples. |

### Reference

| Page | Description |
|---|---|
| [Compiler Options — CPU](docs/compiler_options_cpu.html) | Output formats, target architecture, optimization, parallelism, and debug flags. |
| [Compiler Options — NNPA](docs/compiler_options_nnpa.html) | NNPA acceleration, placement heuristic, quantization, dynamic shapes, and device placement. |
| [Troubleshooting and Debug](docs/troubleshooting.html) | Debug symbols, profiling, instrumentation options, and the NNPA unsupported ops report. |
| [Scope and Versioning](docs/versioning.html) | Supported ONNX operations, release cadence, and compatibility policy. |

| [Verified ONNX Models](https://github.com/IBM/zDLC/blob/main/models/README.md) | Full list of ONNX Model Zoo models tested with IBM zDLC. |

---

## Quick start

```bash
# 1. Pull the compiler image
ZDLC_IMAGE=icr.io/ibmz/zdlc:5.1.0
docker pull ${ZDLC_IMAGE}

# 2. Clone this repository
git clone https://github.com/IBM/zDLC
ZDLC_DIR=$(pwd)/zDLC

# 3. Compile a model
docker run --rm -v ${ZDLC_DIR}/models:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz --maccel=NNPA \
  mnist-12.onnx
```

See [Getting Started](docs/getting_started.md) for the full step-by-step guide.

---

## License

[Apache 2.0](LICENSE)
