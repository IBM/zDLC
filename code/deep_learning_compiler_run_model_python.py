import json
import os
import numpy as np
from PyRuntime import ExecutionSession

class DLCModelExample:

    def __init__(self):
        model_name = '/model/mobilenetv2-7.so'
        if os.path.exists(model_name):
            self.model = model_name
        else:
            raise FileNotFoundError("The compiled model was not found. Please reference instructions on how to build a model and try again.")

        # Instantiate a inference session.
        self.session = ExecutionSession(self.model)

        # Load the input tensor dimensions.
        # { "type" : "f32" , "dims" : [-1 , 3 , 224 , 224] , "name" : "input" }
        # Note here that a -1 indicates a dynamic batch size in the model
        # and that some models may require multiple input tensors.
        self.dims = json.loads(self.session.input_signature())[0]["dims"]

        # Model input signatures use -1 to indicate sizes that can vary at runtime.
        # For mobilenetv2-7, the batch size is dynamic. Use 1 for this
        # dimension so we can generate input data.
        self.dims = [1 if dim == -1 else dim for dim in self.dims]
        np.random.seed()

        # Generate a random input tensor for our model.
        self.input_data = np.random.rand(*self.dims).astype('float32')

    def run_inference(self):
        print("The input tensor dimensions are:")
        print(self.dims)
        # Run the inference session.
        outputs = self.session.run(self.input_data)
        print("A brief overview of the output tensor is:")
        # Look at the output tensor. Similarly, some models
        # also generate multiple output tensors, so we need
        # to index into the tensor list and index the first
        # tensor.
        print(outputs[0][0:5])
        print("The dimensions of the output tensor are:")
        # Review the output tensor shape.
        print(outputs[0].shape)

if __name__ == '__main__':
    model_example = DLCModelExample()
    model_example.run_inference()
