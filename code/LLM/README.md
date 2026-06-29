# LLM Code Examples with IBM Z Deep Learning Compiler(zDLC) <a id="llm-example"></a>

## Overview

This directory contains code examples demonstrating how to use [**zdlc**](https://github.com/IBM/zDLC) (IBM z Deep Learning Compiler) to leverage encoder models on IBM z17 systems. The zdlc framework enables efficient deployment of Large Language Models (LLMs) by utilizing the specialized AI acceleration capabilities of the z17 architecture.

## LLM Models

The examples in this directory demonstrate various encoder-based LLM models, including:

- **BERT** (Bidirectional Encoder Representations from Transformers)
- Other transformer-based encoder architectures

## Use Cases

### Semantic Search Embeddings 

BERT model can output contextual embeddings. This is useful for:

    - Semantic Similarity
    - Duplicate Detection
    - Recommendation Systems

### Masked Language Modeling (MLM)

Encoder models like BERT can take a sentece with a masked input [MASK], then run the entire masked sentence through the model and predict the masked word.

### Question Answering (QNA)

Encoder models like BERT excel at understanding context and extracting relevant information from text. The QNA examples demonstrate:

- Reading comprehension tasks
- Extracting answers from given passages

### Text Summarization

The summarization examples showcase how encoder models can:

- Extract key information from longer documents
- Generate concise summaries while preserving meaning

## Getting Started

The following contains:

- Model-specific implementation code
- Sample input data
- Configuration files for zdlc compilation
- Instructions for running inference on z17

## Benefits of z17 Acceleration

Using zdlc with z17 hardware provides:

- **Performance**: Hardware-accelerated inference for faster processing
- **Efficiency**: Reduced latency for real-time applications
- **Scalability**: Handle larger workloads with optimized resource utilization

<br>

## Download the IBM Z Deep Learning Compiler container <a id="container"></a>

Downloading the IBM Z Deep Learning Compiler image requires
credentials for the `icr.io` registry. Information on obtaining the credentials
is located at [IBM Z and LinuxONE Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).
<br>

Determine the desired versions of the zdlc image to download from the [IBM Z and LinuxOne Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).

Set the enviorment variable based on the desired image version:

```
ZDLC_IMAGE=icr.io/ibmz/zdlc:[version]
```
<br>

Pull the images as shown:

```
docker pull ${ZDLC_IMAGE}
```

| Variable | Description |
| -------- | ----------- |
|ZDLC_IMAGE=icr.io/ibmz/zdlc:[version]|Set [version] based on the desired version in IBM Z and LinuxONE Container Registry.|

<br>

## Download the IBM Z Deep Learning Compiler examples <a id="clone_examples"></a>
<br>

The code examples are located in this GitHub repository. The easiest way to
follow the examples is to clone the example code repository to your local system.

To clone the example repository to a new subdirectory called `zDLC`:
```
git clone https://github.com/IBM/zDLC
```

<br>

Set ZDLC_DIR to where you cloned this example repository:
```
ZDLC_DIR=$(pwd)/zDLC
```
This assumes you cloned the repository to the current working directory using
the `git clone` command above. If you cloned the repository to another location,
make sure to set this variable accordingly.

| Variable | Description |
| -------- | ----------- |
|ZDLC_DIR=$(pwd)/zDLC| `$(pwd)` resolves to the current working directory. <br> `zDLC` is the name of this repository. The zDLC directory is created automatically by `git clone`.

<br>

## Environment variables <a id="setvars"></a>

Set the environment variables for use with the IBM Z Deep Learning Compiler
container image. The environment variables will simplify the container commands
throughout the rest of this document. See the description in the table below for
additional information.

NOTE: ZDLC_IMAGE and ZDLC_DIR are based on your local system. To set these
environment variables, see:
* [Download the IBM Z Deep Learning Compiler containers](#container)
* [Download the IBM Z Deep Learning Compiler example repository](#clone_examples)


```
ZDLC_CODE_DIR=${ZDLC_DIR}/code/LLM
ZDLC_LIB_DIR=${ZDLC_DIR}/lib
ZDLC_MODEL_DIR=${ZDLC_DIR}/models
ZDLC_MODEL_NAME=bert-large-uncased
ZDLC_MODEL_TASK=MLM
if [ -z ${ZDLC_IMAGE} ]; then echo ERROR: ZDLC_IMAGE must be set first; fi
if [ -z ${ZDLC_DIR} ] || [ ! -d ${ZDLC_DIR} ]; then echo ERROR: ZDLC_DIR must be set to an existing zDLC example directory first; fi
```

| Variable | Description |
| -------- | ----------- |
| ZDLC_CODE_DIR=${ZDLC_DIR}/code | Used in:<br>• [Downloading the LLM ONNX file](#download-onnx)<br>• [Running the LLM inference Python example](#llm-run) |
| ZDLC_LIB_DIR=${ZDLC_DIR}/lib | Used in:<br>• [Running the LLM inference Python example](#llm-run) |
| ZDLC_MODEL_DIR=${ZDLC_DIR}/models | Used in:<br>• [Downloading the LLM ONNX file](#download-onnx)<br>• [Building the LLM .so using the IBM Z Deep Learning Compiler](#so-llm)<br>• [Downloading the LLM ONNX file](#download-onnx)<br>• [Running the LLM inference Python example](#llm-run) |
| ZDLC_MODEL_NAME=bert-large-uncased | Used in:<br>• [Downloading the LLM ONNX file](#download-onnx)<br>• [Building the LLM .so using the IBM Z Deep Learning Compiler](#so-llm)<br>• [Running the LLM inference Python example](#llm-run) |
| ZDLC_MODEL_TASK=MLM | Used in:<br>• [Downloading the LLM ONNX file](#download-onnx)<br>• [Running the LLM inference Python example](#llm-run) |
| if ... fi | Simple tests to confirm ZDLC_IMAGE and ZDLC_DIR were set. If they were not set, set them and then reset the other variables.

<br>

## Building the LLM example container <a id="build-llm-container"></a>

This container contains Python and the required libraries to pull a BERT model from Hugging Face and convert it into an ONNX model
that IBM ZDLC supports. It uses the IBM Z Accelerated for Pytorch image as the base image. 

```
docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) -f ${ZDLC_DIR}/docker/Dockerfile.llm -t zdlc-llm-example .
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker build | Build the container image. |
| --build-arg UID=$(id -u) | Set UID in the Dockerfile to the User ID of the user building the container. |
| --build-arg GID=$(id -g) | Set GID in the Dockerfile to the Group ID of the user building the container. |
| -f docker/Dockerfile.llm | Use `docker/Dockerfile.llm` as the Dockerfile for this container build. |
| -t zdlc-llm-example:latest | Build the image with the `image:tag` specification of `zdlc-llm-example`. |

## Download and convert a BERT model from Hugging Face <a id="download-onnx"></a>

Run the `download_bert_model.py` script to download and convert a BERT model from Hugging Face into an ONNX model. This script contains multiple use cases please refer to the `--help` for further explanation of its capabilities. 

```
docker run --rm --user $(id -u):$(id -g) --userns=keep-id -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_MODEL_DIR}:/models:z --env PYTHONPATH=/build/lib zdlc-llm-example:latest /code/download_bert_model.py --model-type ${ZDLC_MODEL_TASK} --model-name ${ZDLC_MODEL_NAME}
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| --user $(id -u):$(id -g) | Set User ID and Group ID inside container to the User ID and Group ID of the user running the container. |
| --userns=keep-id | Tells the container to use your same user and group IDs inside the container |
| -v ${ZDLC_CODE_DIR}:/code:z | The `/code` host bind mount points to the directory with the calling program. `:z` is required to share the volume if SELinux is installed. |
| -v ${ZDLC_MODEL_DIR}:/models:z | The `/model` host bind mount points to the directory with the model `.so` file. `:z` is required to share the volume if SELinux is installed. |
| --env PYTHONPATH=/build/lib | When the container is launched, the `PYTHONPATH` environment variable is set up to point to `/build/lib` directory containing the PyRuntime library needed for execution. |
| -t zdlc-llm-example:latest | Build the image with the `image:tag` specification of `zdlc-llm-example`. |
| --model-type ${ZDLC_MODEL_TASK} | Set the BERT model to contain a masked language model head. |
| --model-name ${ZDLC_MODEL_TASK} | Use bert-large-uncased as the base model. |

## IBM Z Deep Learning Compiler command line interface help <a id="cli-help"></a>

Running the IBM Z Deep Learning Compiler container image with no parameters
shows the complete help for the IBM Z Deep Learning Compiler.

```
docker run --rm ${ZDLC_IMAGE}
```

Note the command line entry point for the IBM Z Deep Learning Compiler is the
`zdlc` command. The IBM Z Deep Learning Compiler is invoked by running the
`zdlc` image with the `docker run` command.

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |

The help for the IBM Z Deep Learning Compiler can also be displayed by
adding the `--help` option to the command line.

<br>

## Building the BERT .so using the IBM Z Deep Learning Compiler <a id="so-llm"></a>

Use the `--EmitLib` option to build a `.so` shared library of the model specified by ZDLC_MODEL_NAME in [Environment variables](#setvars):

```
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz --maccel=NNPA ${ZDLC_MODEL_NAME}/${ZDLC_MODEL_NAME}.onnx
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| ZDLC_MODEL_NAME | Name of the model to compile without ending suffix. |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_MODEL_DIR}:/workdir:z | The host bind mount points to the directory with the model ONNX file. `:z` is required to share the volume if SELinux is installed. |
| --EmitLib | Build the `.so` shared library of the model. |
| --O3 | Optimize to the highest level. |
| -march=z17 | The minimum CPU architecture (for generated code instructions). 
The `--mcpu` option is now replaced with the `-march` option. The `--mcpu` option is still supported but will be deprecated in the future. |
| --mtriple=s390x-ibm-loz | The target architecture for generated code. |
| --maccel=NNPA | The target IBM Z Integrated Accelerator for AI. |
| ${ZDLC_MODEL_NAME}.onnx | Builds the `.so` shared library from the specified ONNX file. |

### Optional: NNPA dynamic quantization of the BERT model

NNPA in IBM Telum II supports 8-bit signed-integer quantized matrix multiplications. Please refer to [ONNX-MLIR's NNPA Quantization Overview](https://github.com/onnx/onnx-mlir/blob/main/docs/Quantization-NNPA.md) for the other quantization options and more information. 

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| --nnpa-quant-dynamic | The compiler will decide quantization options and operation types by itself. |

The built `.so` shared library is written to the host bind mount location.

## Running the BERT masked language model inference Python example <a id="llm-run"></a>

This example program is written in Python and runs using the Python runtime.
The example program calls the ONNX-MLIR Runtime APIs by leveraging
[pybind and PyExecutionSession](http://onnx.ai/onnx-mlir/UsingPyRuntime.html)
which is best described in sections `Using PyRuntime` and `PyRuntime Module`
in the linked documentation.

If not already compiled, compile the model specified by ZDLC_MODEL_NAME in [Environment variables](#setvars) to a [.so shared library](#so-llm)
as described previously.

Next, copy the PyRuntime library out of the Docker container using:

```
mkdir -p ${ZDLC_LIB_DIR}
docker run --rm -v ${ZDLC_LIB_DIR}:/files:z --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} -c "cp /usr/local/lib/PyRuntime* /files"
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_LIB_DIR}:/files:z | The `/files` host bind mount points to the directory we want to contain the PyRuntime library. `:z` is required to share the volume if SELinux is installed. |
| --entrypoint '/usr/bin/bash' | The user will enter the container with `/usr/bin/bash` as the starting process. |
| -c "cp" | Tell the entrypoint bash process to copy the PyRuntime library outside of the container into the directory bind mounted at `/files`. |

Run this optional step to see the files that were copied.

```
ls -laR ${ZDLC_LIB_DIR}
```

Now, run the `llm_example.py` script with the flag `--task MLM` to fill in a masked word on the given masked sentence. This script contains multiple use cases please refer to the `--help` for further explanation of its capabilities. 

```
docker run --rm -v ${ZDLC_LIB_DIR}:/build/lib:z -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_MODEL_DIR}:/models:z --env PYTHONPATH=/build/lib zdlc-llm-example:latest /code/llm_example.py --task ${ZDLC_MODEL_TASK} --text-one "The capital of [MASK] is paris" --model ${ZDLC_MODEL_NAME}
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_CODE_DIR}:/code:z | The `/code` host bind mount points to the directory with the calling program. `:z` is required to share the volume if SELinux is installed. |
| -v ${ZDLC_LIB_DIR}:/build/lib:z | The `/build/lib` host bind mount points to the directory containing the PyRuntime library. `:z` is required to share the volume if SELinux is installed. |
| -v ${ZDLC_MODEL_DIR}:/models:z | The `/model` host bind mount points to the directory with the model `.so` file. `:z` is required to share the volume if SELinux is installed. |
| --env PYTHONPATH=/build/lib | When the container is launched, the `PYTHONPATH` environment variable is set up to point to `/build/lib` directory containing the PyRuntime library needed for execution. |
| -t zdlc-llm-example:latest | Build the image with the `image:tag` specification of `zdlc-llm-example`. |
| --model-type ${ZDLC_MODEL_TASK} | Set the script's use case to masked language modeling. |
| --text-one "The capital of [MASK] is paris" | The masked sentence to run the model on. |
| --model-name ${ZDLC_MODEL_NAME}| Use bert-large-uncased as the scripts model. |


### Further examples for extended use cases: 

Note: These commands do not exactly follow the variable conventions in [Environment variables](#setvars) and may require different models to be downloaded via the 
`download_bert_model.py` script. 

Encoding:
```
docker run --rm -v ${ZDLC_LIB_DIR}:/build/lib:z -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_MODEL_DIR}:/models:z --env PYTHONPATH=/build/lib zdlc-llm-example:latest /code/llm_example.py --task EMBED --text-one "Where is Paris?" --model bert-base-uncased
```

Semantic Similarity:
```
docker run --rm -v ${ZDLC_LIB_DIR}:/build/lib:z -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_MODEL_DIR}:/models:z --env PYTHONPATH=/build/lib zdlc-llm-example:latest /code/llm_example.py --task SS --text-one "Where is Paris?" --text-two "Where is France?" --model bert-large-uncased
```

Question and Answering (Requires QNA model):
```
docker run --rm -v ${ZDLC_LIB_DIR}:/build/lib:z -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_MODEL_DIR}:/models:z --env PYTHONPATH=/build/lib zdlc-llm-example:latest /code/llm_example.py --task QNA --text-one "What country is Paris in?" --text-two "Paris is known for love, art, and fashion. Paris is located in France." --model deepset/bert-base-uncased-squad2
```

