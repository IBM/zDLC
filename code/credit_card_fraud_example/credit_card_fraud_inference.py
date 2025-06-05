 # SPDX-License-Identifier: Apache-2.0
 #
 # Copyright contributors to the deep-learning-compiler-container-images project
 #
 # Description: Python Example for running credit card fraud detection model

import sys
import argparse
import os
import numpy as np

from PyRuntime import OMExecutionSession


def process_parameters():
    parser = argparse.ArgumentParser("IBM zDLC Credit Card Fraud Example")
    parser.add_argument("model_so",
                        help=".so Compiled model file")
    return parser.parse_args()

def generate_input():
    # Randomize input data
    dims = [1, 7, 220]
    data_type = np.float32
    input_tensor = np.random.rand(*dims).astype(data_type)

    print(f"Input Tensor has shape {input_tensor.shape} and values:\n{input_tensor}")
    return input_tensor


def main():
    args = process_parameters()
    if not os.path.exists(args.model_so):
        raise FileNotFoundError(
            "The compiled model was not found. Please reference instructions "
            "on how to compile a model and try again.")

    # Instantiate a inference session.
    session = OMExecutionSession(args.model_so)

    # Run the model.
    input_tensor = generate_input()
    output_tensor = session.run(input_tensor)


    print(f"Output Tensor has shape {output_tensor[0].shape} and values:\n{output_tensor[0]}")

if __name__ == '__main__':
    main()