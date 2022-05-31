// SPDX-License-Identifier: Apache-2.0
/*
 * Copyright contributors to the deep-learning-compiler-container-images project
 * 
 */

/*
 * Description: Java Example for calling model APIs
 */

import com.ibm.onnxmlir.OMModel;
import com.ibm.onnxmlir.OMTensor;
import com.ibm.onnxmlir.OMTensorList;

public class deep_learning_compiler_run_model_example {

    public static void main(String args[]) {

        // The model input signature is returned as JSON output
        // The input signature for the resnet50-caffe2-v1-8 model is:
        // [    { "type" : "f32" , "dims" : [1 , 3 , 224 , 224] , "name" : "gpu_0/data_0" }]
        String modelInputSig = OMModel.inputSignature();

        // Use simple string search to parse the JSON
        int startPos = modelInputSig.indexOf("[");
        startPos = modelInputSig.indexOf("[", startPos + 1);
        int endPos = modelInputSig.indexOf("]", startPos + 1);
        String modelInputDims[] = modelInputSig.substring(startPos + 1, endPos).split(" , *");

        long[] inputTensorShape = new long[modelInputDims.length];
        int inputTensorSize = 1;
        for (int i = 0; i < modelInputDims.length; ++i) {
            long value = Long.valueOf(modelInputDims[i]);
            inputTensorSize *= value;
            inputTensorShape[i] = value;
        }

        float[] inputTensorData = new float[inputTensorSize];
        for (int i = 0; i < inputTensorData.length; ++i) {
            inputTensorData[i] = (float) Math.random()*100;
        }        

        // The resnet50-caffe2-v1-8 model expects a single input tensor
        int numInputTensors = 1;
        OMTensor[] inputTensorsArray = new OMTensor[numInputTensors];

        // Create the single input tensor
        inputTensorsArray[0] = new OMTensor(inputTensorData, inputTensorShape);

        // Some models required multiple input tensors which is supported by adding multiple tensors to the array

        OMTensorList inputTensorListIn = new OMTensorList(inputTensorsArray);

        // Run model
        OMTensorList outputTensorListOut = OMModel.mainGraph(inputTensorListIn);

        // Get results
        OMTensor outputTensor = outputTensorListOut.getOmtByIndex(0);

        long outputTensorLength = outputTensor.getNumElems();
        float prediction[] = outputTensor.getFloatData();

        for (int i=0; i<outputTensorLength; ++i) {
            System.out.println(prediction[i]);
        }

    }
}       
