---
layout: default
title: Use Cases
nav_order: 3
has_children: true
---

# Use Cases

End-to-end examples showing how to compile and deploy AI models on IBM Z with IBM zDLC.

| Use Case | Description |
|---|---|
| [Encoder LLM Inference (BERT)](encoder_llm.html) | BERT inference with NNPA — MLM, embeddings, semantic similarity, QA. |
| [LLM Serving with Triton](triton_llm.html) | Serve zDLC-compiled models via HTTP/gRPC using Triton Inference Server. |
| [Credit Card Fraud Detection](credit_card_fraud.html) | Train, compile, and run accelerated fraud scoring end-to-end. |
| [C++ and Java Inference](cpp_java.html) | Build and run C++ and Java applications against zDLC-compiled models. |
| [Dynamic Shapes](dynamic_shapes.html) | Get maximum NNPA coverage when your model has variable-length inputs like BERT with dynamic sequence length. |
| [Large Models (External Data)](large_models.html) | Compile models over 2 GB by splitting weights to an external data file before compiling. |
| [JSON Configuration File](json_config.html) | Store compile options and control per-operator NNPA placement and quantization in a versioned JSON file. |
| [Debugging with --EmitLLVMIR](llvmir_debugging.html) | Step-by-step workflow for diagnosing wrong model outputs using LLVM IR inspection. |
| [Decoder LLM Inference](decoder_llm.html) | *(Coming soon)* GPT-2 and T5 decoder inference. |
