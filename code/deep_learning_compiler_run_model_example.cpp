// SPDX-License-Identifier: Apache-2.0
/*
 * Copyright contributors to the deep-learning-compiler-container-images project
 *
 */

/*
 * Description: C++ Example for calling model APIs
 */

#include <algorithm>
#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <random>
#include <sstream>
#include <vector>

#include "OnnxMlirRuntime.h"

// Declare the inference entry point.
extern "C" OMTensorList *run_main_graph(OMTensorList *);

float generateRandFloat() {
    return ((float) std::rand()) / (float) RAND_MAX;
}

int main(int argc, char **argv) {

    // The model input signature is returned as JSON output
    // The input signature for the mnist model is:
    // [    { "type" : "f32" , "dims" : [1 , 1 , 28 , 28] , "name" : "Input3" }]
    std::string modelInputSig = omInputSignature("run_main_graph");

    // Use simple string search to parse the JSON
    std::vector<int64_t> inputTensorShape;
    int64_t inputTensorSize = 1;

    size_t startPos = modelInputSig.find("[");
    startPos = modelInputSig.find("[", startPos + 1);
    size_t endPos = modelInputSig.find("]", startPos + 1);
    std::istringstream modelInputDims(modelInputSig.substr(startPos + 1, endPos - startPos - 1));
    std::string token;
    while(getline(modelInputDims, token, ',')) {
        int64_t value = atoi(token.c_str());
        inputTensorSize *= value;
        inputTensorShape.push_back(value);
    }

    std::vector<float> inputTensorData(inputTensorSize);
    std::generate(inputTensorData.begin(), inputTensorData.end(), generateRandFloat);

    int64_t inputTensorRank = inputTensorShape.size();

    // The mnist model expects a single input tensor
    size_t numInputTensors = 1;
    OMTensor* inputTensorsArray[numInputTensors];

    // Create the single input tensor
    inputTensorsArray[0] = omTensorCreate(inputTensorData.data(), inputTensorShape.data(), inputTensorRank, ONNX_TYPE_FLOAT);

    // Some models required multiple input tensors which is supported by adding multiple tensors to the array

    OMTensorList *inputTensorListIn = omTensorListCreate(inputTensorsArray, numInputTensors); // 1 = Single input tensor

    // Run model
    OMTensorList *outputTensorListOut = run_main_graph(inputTensorListIn);

    // If an error occurs during inferencing, NULL is returned for the list of output tensors.
    if (outputTensorListOut == NULL) {
        std::cout << "run_main_graph encountered an error: " << strerror(errno) << std::endl;
        exit(-1);
    }

    // Get results
    OMTensor *outputTensor = omTensorListGetOmtByIndex(outputTensorListOut, 0); // 0 = The first output tensor

    int64_t outputTensorLength = omTensorGetNumElems(outputTensor);
    float *oDataPtr = (float *)omTensorGetDataPtr(outputTensor);

    for (int i=0; i < outputTensorLength; ++i)
        std::cout << oDataPtr[i] << std::endl;

    // The caller is responsible for destroying these lists
    omTensorListDestroy(inputTensorListIn);
    omTensorListDestroy(outputTensorListOut);

    return 0;
}

