// SPDX-License-Identifier: Apache-2.0
/*
 * Copyright contributors to the deep-learning-compiler-container-images project
 *
 */

/*
 * Description: Java Example for calling model APIs
 */

import java.util.ArrayList;
import java.util.Arrays;

import com.ibm.onnxmlir.OMModel;
import com.ibm.onnxmlir.OMTensor;
import com.ibm.onnxmlir.OMTensorList;

public class deep_learning_compiler_run_model_example {

    public static OMTensorList generateInput() throws Exception {
        ArrayList<OMTensor> inputTensorArrayList = new ArrayList<OMTensor>();

        // The model input signature is returned as JSON output
        // The input signature for the resnet50-caffe2-v1-8 model is:
        // [    { "type" : "f32" , "dims" : [1 , 3 , 224 , 224] , "name" : "gpu_0/data_0" }]
        String modelInputSig = OMModel.inputSignature();

        // Use string search to parse the JSON and generate random input values.
        int tensorStrStart = 0, tensorStrEnd = 0;
        while (tensorStrStart < modelInputSig.lastIndexOf("}")) {
            // Each input tensor is wrapped in {}'s
            tensorStrStart = modelInputSig.indexOf("{", tensorStrStart) + 1;
            tensorStrEnd = modelInputSig.indexOf("}", tensorStrStart);
            String tensorStr = modelInputSig.substring(
                tensorStrStart, tensorStrEnd);

            // The shape for each input tensor is wrapped in []'s.
            int dimStart = modelInputSig.indexOf("[", tensorStrStart) + 1;
            int dimEnd = modelInputSig.indexOf("]", tensorStrStart);
            String dimsStr[] = modelInputSig.substring(
                dimStart, dimEnd).split(" , *");

            // Convert shape strings to numeric values.
            long[] inputShape = new long[dimsStr.length];
            int inputSize = 1;
            boolean foundDynamicDim = false;
            for (int i = 0; i < inputShape.length; i++) {
                long value = Long.valueOf(dimsStr[i]);
                if (value == -1 ) {
                    if (foundDynamicDim) {
                        throw new Exception(
                            "Example client only supports a single dynamic "+
                            "dimension (-1). However multiple dynamic " +
                            "dimensions were found for input " + tensorStr);
                    } else {
                        value = 1;
                        foundDynamicDim = true;
                    }
                }
                inputSize *=value;
                inputShape[i] = value;
            }

            if (!tensorStr.contains("f32")) {
                throw new Exception(
                    "Example client only supports signature type: f32 but got type " +
                    tensorStr);
            }

            // Generate a random input tensor for our model.
            float[] inputData = new float[inputSize];
            for (int i = 0; i < inputData.length; i++) {
                inputData[i] = (float) Math.random() * 100;
            }

            // Shift down the string for the next iteration
            tensorStrStart = tensorStrEnd;

            // Add input tensor to input list
            inputTensorArrayList.add(new OMTensor(inputData, inputShape));
        }

        // Inference input needs to be an OMTensorList which requires an Array
        OMTensor[] inputTensorArray = inputTensorArrayList.toArray(new OMTensor[0]);
        return new OMTensorList(inputTensorArray);
    }

    public static void main(String args[]) throws Exception {
        OMTensorList inputOMTensorList = generateInput();

        // Run the model.
        OMTensorList outputOMTensorList = OMModel.mainGraph(inputOMTensorList);
        OMTensor[] outputTensorArray = outputOMTensorList.getOmtArray();

        // Print results.
        for (int tensorIdx = 0; tensorIdx < outputTensorArray.length; tensorIdx++ ) {
            OMTensor outputTensor = outputTensorArray[tensorIdx];
            System.out.print(
                "output_tensor[" + tensorIdx + "] " +
                "has shape " + Arrays.toString(outputTensor.getShape()) + " " +
                "and values ");
            switch(outputTensor.getDataType()) {
                case OMTensor.ONNX_TYPE_BOOL:
                    System.out.println("of type bool[]:");
                    byte[] bool_bytes = outputTensor.getBoolData();
                    for (int valueIdx = 0; valueIdx < outputTensor.getNumElems(); ++valueIdx) {
                         System.out.println("\t" + bool_bytes[valueIdx]);
                    }
                    break;
                case OMTensor.ONNX_TYPE_INT8:
                case OMTensor.ONNX_TYPE_UINT8:
                    System.out.println("of type byte[]:");
                    byte[] int_bytes = outputTensor.getByteData();
                    for (int valueIdx = 0; valueIdx < outputTensor.getNumElems(); ++valueIdx) {
                         System.out.println("\t" + int_bytes[valueIdx]);
                    }
                    break;
                case OMTensor.ONNX_TYPE_INT16:
                case OMTensor.ONNX_TYPE_UINT16:
                    System.out.println("of type short[]:");
                    short[] shorts = outputTensor.getShortData();
                    for (int valueIdx = 0; valueIdx < outputTensor.getNumElems(); ++valueIdx) {
                         System.out.println("\t" + shorts[valueIdx]);
                    }
                    break;
                case OMTensor.ONNX_TYPE_INT32:
                case OMTensor.ONNX_TYPE_UINT32:
                    System.out.println("of type int[]:");
                    int[] ints = outputTensor.getIntData();
                    for (int valueIdx = 0; valueIdx < outputTensor.getNumElems(); ++valueIdx) {
                         System.out.println("\t" + ints[valueIdx]);
                    }
                    break;
                case OMTensor.ONNX_TYPE_INT64:
                case OMTensor.ONNX_TYPE_UINT64:
                    System.out.println("of type long[]:");
                    long[] longs = outputTensor.getLongData();
                    for (int valueIdx = 0; valueIdx < outputTensor.getNumElems(); ++valueIdx) {
                         System.out.println("\t" + longs[valueIdx]);
                    }
                    break;
                case OMTensor.ONNX_TYPE_FLOAT:
                    System.out.println("of type float[]:");
                    float[] floats = outputTensor.getFloatData();
                    for (int valueIdx = 0; valueIdx < outputTensor.getNumElems(); ++valueIdx) {
                         System.out.println("\t" + floats[valueIdx]);
                    }
                    break;
                case OMTensor.ONNX_TYPE_DOUBLE:
                    System.out.println("of type double[]:");
                    double[] doubles = outputTensor.getDoubleData();
                    for (int valueIdx = 0; valueIdx < outputTensor.getNumElems(); ++valueIdx) {
                         System.out.println("\t" + doubles[valueIdx]);
                    }
                    break;
                default:
                    throw new Exception(
                        "Example client doesn't support output tensors with " +
                        "OMTensor type " + outputTensor.getDataType());
            }
        }
    }
}
