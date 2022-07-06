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

OMTensorList* generate_input(std::vector<OMTensor *>& input_tensor_vector){
    // The model input signature is returned as JSON output
    // The input signature for the mnist model is:
    // [    { "type" : "f32" , "dims" : [1 , 1 , 28 , 28] , "name" : "Input3" }]
    std::string model_input_sig = omInputSignature("run_main_graph");

    // Use string search to parse the JSON and generate random input values.

    size_t tensor_str_start = 0, tensor_str_end = 0;
    while (tensor_str_start < model_input_sig.rfind("}")) {
        // Each input tensor is wrapped in {}'s
        tensor_str_start = model_input_sig.find("{", tensor_str_start) + 1;
        tensor_str_end = model_input_sig.find("}", tensor_str_start);
        std::string tensor_str = model_input_sig.substr(
            tensor_str_start, tensor_str_end - tensor_str_start);

        // The shape for each input tensor is wrapped in []'s.
        int dim_start = model_input_sig.find("[", tensor_str_start) + 1;
        int dim_end = model_input_sig.find("]", tensor_str_start);
        std::string dim_str = model_input_sig.substr(
            dim_start, dim_end - dim_start);
        std::istringstream dim_str_stream(dim_str);

        std::vector<int64_t> input_shape;
        int64_t input_size = 1;
        bool found_dynamic_dim = false;
        std::string token;
        while(getline(dim_str_stream, token, ',')) {
            int64_t value = atoi(token.c_str());
            if (value == -1 ) {
                if (found_dynamic_dim) {
                    std::cout <<
                        "Example client only supports a single dynamic " <<
                        "dimension (-1). However multiple dynamic " <<
                        "dimensions were found for input " << tensor_str << std::endl;
                        exit(-1);
                } else {
                    value = 1;
                    found_dynamic_dim = true;
                }
            }
            input_size *=value;
            input_shape.push_back(value);
        }

        if (tensor_str.find("f32") == std::string::npos) {
            std::cout <<
                "Example client only supports signature type: f32 but got " <<
                "type " << tensor_str << std::endl;
            exit(-1);
        }

        // Generate a random input tensor for our model.
        float *input_data = new float[input_size];
        for (int i = 0; i < input_size; i++) {
            input_data[i] = ((float) std::rand()) / (float) RAND_MAX;
        }

        // Shift down the string for the next iteration
        tensor_str_start = tensor_str_end;

        // Add input tensor to input list
        // Use CreateWithOwnership(true) in this case so the data array is
        // destroyed with the OMTensor object later.
        OMTensor *input_tensor = omTensorCreateWithOwnership(
            input_data, input_shape.data(), input_shape.size(),
            ONNX_TYPE_FLOAT, true);
        input_tensor_vector.push_back(input_tensor);
    }

    // Use CreateWithOwnership(false) in this case so the OMTensors are NOT
    // destroyed with the OMTensorList object. They will be implicitly
    // destroyed when the input_tensor_vector falls out of its original scope.
    return omTensorListCreateWithOwnership(
        input_tensor_vector.data(), input_tensor_vector.size(), false);
}

int main(int argc, char **argv) {
    std::vector<OMTensor *> input_tensor_vector;
    OMTensorList *input_omtensor_list = generate_input(input_tensor_vector);

    // Run model
    OMTensorList *output_omtensor_list = run_main_graph(input_omtensor_list);

    // If an error occurs during inferencing, NULL is returned.
    if (output_omtensor_list == NULL) {
        std::cout << "run_main_graph encountered an error: " <<
            strerror(errno) << std::endl;
        exit(-1);
    }

    // Get results
    for (int64_t tensor_idx = 0; tensor_idx < omTensorListGetSize(output_omtensor_list); tensor_idx++) {
        OMTensor *output_tensor = omTensorListGetOmtByIndex(
            output_omtensor_list, tensor_idx);
        std::cout << "output_tensor[" << tensor_idx << "] " <<
                "has shape [ ";
        for (int64_t dim_idx = 0; dim_idx < omTensorGetRank(output_tensor); dim_idx++) {
            std::cout << omTensorGetShape(output_tensor)[dim_idx] << " ";
        }
        std::cout << "] and values ";

        int64_t num_elements = omTensorGetNumElems(output_tensor);
        switch (omTensorGetDataType(output_tensor)) {
        case ONNX_TYPE_BOOL: {
            std::cout << "of type bool[]:" << std::endl;
            bool *elems = (bool*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_INT8: {
            std::cout << "of type int8_t[]:" << std::endl;
            int8_t *elems = (int8_t*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_UINT8: {
            std::cout << "of type uint8_t[]:" << std::endl;
            uint8_t *elems = (uint8_t*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_INT16: {
            std::cout << "of type int16_t[]:" << std::endl;
            int16_t *elems = (int16_t*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_UINT16: {
            std::cout << "of type uint16_t[]:" << std::endl;
            uint16_t *elems = (uint16_t*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_INT32: {
            std::cout << "of type int32_t[]:" << std::endl;
            int32_t *elems = (int32_t*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_UINT32: {
            std::cout << "of type uint32_t[]:" << std::endl;
            uint32_t *elems = (uint32_t*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_INT64: {
            std::cout << "of type int64_t[]:" << std::endl;
            int64_t *elems = (int64_t*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_UINT64: {
            std::cout << "of type uint64_t[]:" << std::endl;
            uint64_t *elems = (uint64_t*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_FLOAT: {
            std::cout << "of type float[]:" << std::endl;
            float *elems = (float*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        case ONNX_TYPE_STRING: {
            std::cout << "of type char[]:" << std::endl;
            char *elems = (char*)omTensorGetDataPtr(output_tensor);
            for (int elem_idx = 0; elem_idx < num_elements; elem_idx++) {
                std::cout << "\t" << elems[elem_idx] << std::endl;
            }
            break;
        }
        default: {
            std::cout << "Example client doesn't support output tensors " <<
                "with OMTensor type " << omTensorGetDataType(output_tensor) <<
                std::endl;
        }
        }
    }

    // The caller is responsible for destroying these lists
    omTensorListDestroy(input_omtensor_list);
    omTensorListDestroy(output_omtensor_list);

    return 0;
}
