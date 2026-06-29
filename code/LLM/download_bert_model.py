 # SPDX-License-Identifier: Apache-2.0
 #
 # Copyright contributors to the deep-learning-compiler-container-images project
 #
 # Description: Python Example for downloading variations of the encoder BERT model

import argparse
import sys
import torch
import traceback

from transformers import AutoTokenizer, AutoModelForQuestionAnswering, BertModel, BertTokenizer, BertForMaskedLM

# Supported models and tasks
SUPPORTED_MODELS = {"bert-base-uncased", "bert-large-uncased", "deepset/bert-base-uncased-squad2"}
SUPPORTED_TYPES = {"EMBED", "MLM", "QNA"}
MODEL_COMPATIBILITY = {
    "bert-base-uncased": {"EMBED", "MLM"},
    "bert-large-uncased": {"EMBED", "MLM"},
    "deepset/bert-base-uncased-squad2": {"QNA"},
}

def parse_args():
    parser = argparse.ArgumentParser(description="Download a BERT model and export to ONNX.")
    parser.add_argument("--model-name", type=str, choices=SUPPORTED_MODELS, required=True, help="Name of the BERT model to download.")
    parser.add_argument("--model-type", type=str, choices=SUPPORTED_TYPES, required=True, help="Model types: EMBED, MLM or QNA")
    parser.add_argument("--output-dir", type=str, default="/models", help="Output directory for models (default: /models for container")

    args = parser.parse_args()
    if args.model_type not in MODEL_COMPATIBILITY[args.model_name]:
        raise ValueError( f"Incompatible selection: model '{args.model_name}' does not support '{args.model_type}")
    return args

def get_model(model_type: str, model_name: str):
    """
    Load the appropriate model for ONNX export.
    """
    if model_type == "EMBED":
        model = BertModel.from_pretrained(model_name)
    elif model_type == "MLM":
        model = BertForMaskedLM.from_pretrained(model_name)
    elif model_type == "QNA":
        model = AutoModelForQuestionAnswering.from_pretrained(model_name)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    return model

def get_input_text(model_type: str):
    """
    Generate the appropriate text input for ONNX export.
    """
    example_text_two = ""
    if model_type == "EMBED":
        example_text = "My name is test."
    elif model_type == "MLM":
        example_text = "My name is [MASK]."
    elif model_type == "QNA":
        example_text = "What is my name?"
        example_text_two = "My name is test."
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    return example_text, example_text_two

def get_tokenizer(model_type: str, model_name: str):
    """
    Load the appropriate tokenizer for ONNX export.
    """
    if model_type == "EMBED" or model_type == "MLM":
        tokenizer = BertTokenizer.from_pretrained(model_name)
    elif model_type == "QNA":
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    return tokenizer

def tokenize(model_type: str, text: str, context: str, tokenizer):
    """
    Tokenize the input for ONNX export.
    """
    if model_type == "EMBED" or model_type == "MLM":
        tokens = tokenizer(text, return_tensors="pt") 
    elif model_type == "QNA":
        tokens = tokenizer(text, context, return_tensors="pt") 
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    return tokens

def get_dynamic_axes(model_type: str):
    """
    Format dyanmic axes for ONNX export.
    """
    dynamic_axes = {
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "token_type_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
    }
    if model_type == "EMBED":
        dynamic_axes.update({
            "last_hidden_state": {0: "batch_size", 1: "sequence_length"},
            "pooler_output": {0: "batch_size"}
        })
    elif model_type == "MLM":
        dynamic_axes.update({
            "logits": {0: "batch_size", 1: "sequence_length"}
        })
        
    elif model_type == "QNA":
        dynamic_axes.update({
            "start_logits": {0: "batch_size", 1: "sequence_length"},
            "end_logits": {0: "batch_size", 1: "sequence_length"}
        })
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    return dynamic_axes

def main():
    args = parse_args()
    model_name = args.model_name
    model_type = args.model_type
    output_dir = args.output_dir
    print(f"Downloading model: {model_name} for model type: {model_type}")

    # Save model and metadata to models directory
    local_model_dir = f"{output_dir}/{model_name.replace('/', '-')}"

    # Load Tokenizer, Model, and Save
    tokenizer = get_tokenizer(model_type, model_name)
    tokenizer.save_pretrained(local_model_dir)
    model = get_model(model_type, model_name)
    model.save_pretrained(local_model_dir)
    print(f"Model and tokenizer saved to {local_model_dir}")

    # Tokenize the input
    input_one, input_two = get_input_text(model_type)
    input = tokenize(model_type, input_one, input_two, tokenizer)

    # Forward pass once to ensure model is ready
    output = model(**input)

    # The onnx graph export requires 'attention_mask' to be positionally second in the input 
    input_keys = ["input_ids", "attention_mask", "token_type_ids"]
    output_keys = list(output.keys())
    print(f"input_keys: {input_keys}")
    print(f"output_keys: {output_keys}")

    # Export ONNX Model
    onnx_model_path = f"{local_model_dir}/{model_name.replace('/', '-')}.onnx"
    dynamic_axes = get_dynamic_axes(model_type)
    
    print(f"Starting ONNX export to {onnx_model_path}...", flush=True)
    print(f"Model type: {type(model)}", flush=True)
    print(f"Input shapes: input_ids={input['input_ids'].shape}, attention_mask={input['attention_mask'].shape}, token_type_ids={input['token_type_ids'].shape}", flush=True)
    
    try:
        print("Calling torch.onnx.export() with dynamo=True...", flush=True)
        torch.onnx.export(
            model,
            (input["input_ids"], input["attention_mask"], input["token_type_ids"]),
            onnx_model_path,
            input_names=input_keys,
            output_names=output_keys,
            dynamic_axes=dynamic_axes,
            do_constant_folding=False,
            opset_version=18,
            verbose=False
        )
        print(f"Model successfully converted to ONNX format and saved to {onnx_model_path}", flush=True)
    except Exception as e:
        print(f"ERROR: ONNX export failed: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
    
    # Verify file was created
    import os
    if not os.path.exists(onnx_model_path):
        print(f"ERROR: ONNX file was not created at {onnx_model_path}", flush=True)
        sys.exit(1)
    
    print(f"ONNX export completed successfully", flush=True)
    # Bypass Python interpreter shutdown with os._exit() to avoid an s390x
    # segfault in upb_DefPool_Free during protobuf DescriptorPool teardown.
    # The .onnx file is already written and stdout is flushed, so skipping
    # finalization is safe. Without this, CI sees exit code 139 despite a
    # successful export. Related: PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
    # in the Dockerfile.llm fixes the analogous import-time crash.
    os._exit(0)

if __name__ == "__main__":
    main()

