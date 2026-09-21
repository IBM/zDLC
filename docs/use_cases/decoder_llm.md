# Use Case: Decoder LLM Inference

> **Coming Soon**
>
> This section will cover running decoder-based (generative) LLM inference on IBM Z using IBM zDLC, including examples with GPT-2 and T5.

---

## Planned content

- Exporting decoder models (GPT-2, T5) to ONNX format
- Compiling decoder models with IBM zDLC and NNPA acceleration
- End-to-end text generation example
- Encoder-decoder pipelines (e.g. T5 encoder + T5 decoder with LM head)
- Performance considerations specific to autoregressive decoding on IBM Z

---

## Already verified decoder models

The following decoder and encoder-decoder models from the ONNX Model Zoo have already been built and verified with IBM zDLC:

| Model | Type |
|---|---|
| [gpt2-10](https://github.com/onnx/models/tree/main/validated/text/machine_comprehension/gpt-2) | Decoder |
| [gpt2-lm-head-10](https://github.com/onnx/models/tree/main/validated/text/machine_comprehension/gpt-2) | Decoder with LM head |
| [t5-encoder-12](https://github.com/onnx/models/tree/main/validated/text/machine_comprehension/t5) | Encoder |
| [t5-decoder-with-lm-head-12](https://github.com/onnx/models/tree/main/validated/text/machine_comprehension/t5) | Decoder with LM head |

See [models/README.md](../../models/README.md) for the full verified model list.

---

In the meantime, refer to [Encoder LLM Inference](encoder_llm.md) for a complete end-to-end example, and [Getting Started](../getting_started.md) to compile any ONNX model manually.
