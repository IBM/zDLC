import argparse
import json
import numpy as np
import os
import sys

from PyRuntime import OMExecutionSession


def process_parameters():
    parser = argparse.ArgumentParser("IBM zDLC Python example")
    parser.add_argument("model_so",
                        help=".so Compiled model file")
    return parser.parse_args()

def get_np_type(signature_type):
    type = {
        "f32": "float32"
    }

    # Model input signature use LLVM types.
    if signature_type not in type.keys():
            raise NotImplementedError(
                "Example client only supports signature types: %s but got %s"
                % (", ".join(type.keys()), signature_type))
    return type[signature_type]

def generate_input(session):
    # Load the input tensor dimensions from the model signature.
    input_signature_json = json.loads(session.input_signature())

    # input for models must be a list of arrays
    input_tensor_list = []

    # Generate a random input tensor for our model.
    np.random.seed()
    for idx, input in enumerate(input_signature_json):
        signature_dims = input["dims"]
        signature_type = input["type"]

        # Model input signatures use -1 to indicate dimensions that can vary at
        # runtime. Often this is a dynamic batch size but some models also have
        # dynamic image shapes which is not supported in this example.
        if signature_dims.count(-1) > 1:
            raise NotImplementedError(
                "Example client only supports a single dynamic dimension (-1). "
                "However multiple dynamic dimensions were found for "
                "input[%d] with shape %s"
                % (idx, signature_dims.shape))

        try:
            np_type = get_np_type(input["type"])
        except NotImplementedError as e:
            raise NotImplementedError(str(e) + " in input[%d]" % idx)

        # Assume remaining dynamic dimension is batch size and set to 1.
        dims = [1 if dim == -1 else dim for dim in signature_dims]
        input_tensor = np.random.rand(*dims).astype(np_type)
        input_tensor_list.append(input_tensor)
        print("input_tensor[%d] has shape %s" % (idx, input_tensor.shape))

    return input_tensor_list

def main():
    args = process_parameters()
    if not os.path.exists(args.model_so):
        raise FileNotFoundError(
            "The compiled model was not found. Please reference instructions "
            "on how to compile a model and try again.")

    # Instantiate a inference session.
    session = OMExecutionSession(args.model_so)

    # Run the model.
    input_tensor_list = generate_input(session)
    output_tensor_list = session.run(input_tensor_list)

    for idx, output_tensor in enumerate(output_tensor_list):
        print("output_tensor[%d] has shape %s and values:\n%s"
              % (idx, output_tensor.shape, output_tensor))

if __name__ == '__main__':
    main()
