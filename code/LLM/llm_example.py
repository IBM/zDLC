 # SPDX-License-Identifier: Apache-2.0
 #
 # Copyright contributors to the deep-learning-compiler-container-images project
 #
 # Description: Python Example for using the encoder BERT model for various inference tasks. 

import argparse
import numpy as np

from PyRuntime import OMExecutionSession
from transformers import AutoTokenizer

# Supported models and tasks
SUPPORTED_MODELS = {"bert-base-uncased", "bert-large-uncased", "deepset/bert-base-uncased-squad2"}
SUPPORTED_TASKS = {"EMBED", "SS", "MLM", "QNA"}
MODEL_COMPATIBILITY = {
    "bert-base-uncased": {"EMBED", "SS", "MLM"},
    "bert-large-uncased": {"EMBED", "SS", "MLM"},
    "deepset/bert-base-uncased-squad2": {"QNA"},
}

def execute_model(model_so, tokens):
    # Run the model with the BERT required onnx-mlir runtime input.
    ort_inputs = [
        tokens["input_ids"],
        tokens["attention_mask"],
        tokens["token_type_ids"],
    ]

    session = OMExecutionSession(model_so)
    output_tensor = session.run(ort_inputs)

    print("\n=== INPUT SIGNATURE ===")
    print(session.input_signature())
    print("\n=== OUTPUT SIGNATURE ===")
    print(session.output_signature())
    return output_tensor

def execute_tokenizer(tokenizer, text, max_length):
    # Tokenize the sentence
    tokens = tokenizer(
        text,
        return_tensors="np",
        max_length=max_length,
        padding="max_length",
        truncation=True,
    )
    return tokens

def execute_tokenizer_for_question_and_answer(tokenizer, question, context, max_length):
    # Tokenize the sentence
    tokens = tokenizer(
        question,
        context,
        return_tensors="np",
        max_length=max_length,
        padding="max_length",
        truncation=True,
    )
    return tokens

def execute_embedding(model_so, tokens):
    # Index all input/output tensors for batch_size = 1
    # Run the model 
    output_tensor = execute_model(model_so, tokens)

    # last_hidden_state (batch_size, sequence_length, hidden_size)
    last_hidden_state = output_tensor[0]

    # Using the attention_mask '1' values to retreive only the non padded tokens int the last_hidden_state output.
    # Large amounts of padded tokens can bias the embedding
    non_pad_tokens = last_hidden_state[0][tokens["attention_mask"][0] == 1]
    embedding = non_pad_tokens.mean(axis=0)

    print("\n=== EMBEDDED VECTOR (preview) ===")
    print("Embedding Shape: ", embedding.shape)
    print(embedding[:5], "...", embedding[-5:])
    return embedding

def execute_semantic_similarity(model_so, tokens_one, tokens_two):
    # Embed both set of tokens
    embedding_one = execute_embedding(model_so, tokens_one)
    embedding_two = execute_embedding(model_so, tokens_two)

    # Similarity comparision
    dot_product_similarity = np.dot(embedding_one, embedding_two)
    cosine_similarity = dot_product_similarity / (np.linalg.norm(embedding_one) * np.linalg.norm(embedding_two))

    print("\n=== SEMANTIC SIMILARITY ===")
    print("Dot Product Similarity: ", dot_product_similarity)
    print("Cosine Similarity: ", cosine_similarity)

def execute_mlm(model_so, tokenizer, tokens):
    # Index all input/output tensors for batch_size = 1
    # Verify sentence has a [MASK] token.
    if tokenizer.mask_token_id not in tokens["input_ids"][0]:
        raise ValueError("The sentence must contain a [MASK] token.")
    else:
        # Find the mask token index
        mask_index = np.where(tokens["input_ids"][0] == tokenizer.mask_token_id)[0][0]
    
    # Run the model 
    output_tensor = execute_model(model_so, tokens)

    # logits (batch_size, sequence_length, vocab_size)
    logits = output_tensor[0]

    # Argmax over vocabulary for MASK positions tensors
    predicted_id = np.argmax(logits[0, mask_index]) 

    # Replace masked token with predicted word
    tokens["input_ids"][0, mask_index] = predicted_id

    # Decode with the Tokenizer
    filled_sentence = tokenizer.decode(tokens["input_ids"][0], skip_special_tokens=True)

    print("\n=== FILLED SENTENCE ===")
    print(filled_sentence)
    return filled_sentence

def execute_question_and_answer(model_so, tokenizer, tokens):
    # Index all input/output tensors for batch_size = 1
    # Run the model 
    output_tensor = execute_model(model_so, tokens)

    # logits (batch_size, sequence_length)
    start_logits = output_tensor[0]
    end_logits = output_tensor[1]

    # Get start and end index 
    start_index = int(np.argmax(start_logits, axis=1)[0])
    end_index = int(np.argmax(end_logits, axis=1)[0])

    # Tokenized ONNX runtime input
    input_ids = tokens["input_ids"]
    token_type_ids = tokens["token_type_ids"] 

    # Decode question (token_type_id=0)
    question_ids = input_ids[token_type_ids == 0]
    question = tokenizer.decode(question_ids, skip_special_tokens=True)

    # Decode context (token_type_id=1)
    context_ids = input_ids[token_type_ids == 1]
    context = tokenizer.decode(context_ids, skip_special_tokens=True)

    #Slice the Answer from the Context 
    answer_ids = input_ids[0, start_index:end_index + 1]
    answer = tokenizer.decode(answer_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True).strip()
    # Non-answer case
    if answer == "": 
        answer = "No Answer Found"

    print("\n=== QUESTION ===")
    print(question)
    print("\n=== CONTEXT ===")
    print(context)
    print("\n=== ANSWER ===")
    print(answer)
    return answer

def get_args():
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(description="Run LLM using zDLC")
    parser.add_argument("--task", type=str, choices=SUPPORTED_TASKS, required=True, help="LLM task you wish to perfrom: " \
        "Embedding (EMBED), Semmantic Similarity (SS), Masked Language Modeling (MLM), and Question and Answering (QNA)")
    parser.add_argument("--text-one", type=str, required=True, help="A piece of text to run a BERT model on")
    parser.add_argument("--text-two", type=str, default="", help="If needed, a second piece of text to run a BERT model on")
    parser.add_argument("--max-length", type=int, default=128, help="Maximum sequence length, per piece of text")
    parser.add_argument("--model-name", type=str, choices=SUPPORTED_MODELS, required=True, help="Model to use for inference")
    args = parser.parse_args()

    args = parser.parse_args()
    if args.task not in MODEL_COMPATIBILITY[args.model_name]:
        raise ValueError( f"Incompatible selection: model '{args.model_name}' does not support '{args.task}")
    return args

if __name__ == "__main__":
    args = get_args()

    model_name = args.model_name
    # Path to model.so inside the container. 
    model_so = f"/models/{model_name}/{model_name}.so"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    match args.task:
        case "EMBED":             
            tokens = execute_tokenizer(tokenizer, args.text_one, args.max_length)
            execute_embedding(model_so, tokens)
        case "SS":
            if args.text_two == "":
                raise ValueError(f"Embedding task for semantic similarity requires a second piece of text to compare")
            
            tokens_one = execute_tokenizer(tokenizer, args.text_one, args.max_length)
            tokens_two = execute_tokenizer(tokenizer, args.text_two, args.max_length)
            execute_semantic_similarity(model_so, tokens_one, tokens_two)
        case "MLM":
            tokens = execute_tokenizer(tokenizer, args.text_one, args.max_length)
            execute_mlm(model_so, tokenizer, tokens)
        case "QNA":
            # Question needed in text-one, Context needed in text-two
            if args.text_two == "":
                raise ValueError(f"Question and Answering requires a second piece of text as the context")
            
            tokens = execute_tokenizer_for_question_and_answer(tokenizer, args.text_one, args.text_two, args.max_length)
            # SPECIAL CASE: Path to model.so inside the container. 
            # deepset/bert-base-uncased-squad2 -> deepset-bert-base-uncased-squad2
            model_so = "/models/deepset-bert-base-uncased-squad2/deepset-bert-base-uncased-squad2.so"
            execute_question_and_answer(model_so, tokenizer, tokens)



            

