# Running the Credit Card Fraud Detection Sample Program <a id="ccfd-example"></a>

## Download the IBM Z Deep Learning Compiler container <a id="container"></a>

Downloading the IBM Z Deep Learning Compiler image requires
credentials for the `icr.io` registry. Information on obtaining the credentials
is located at [IBM Z and LinuxONE Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).
<br>

Determine the desired versions of the zdlc image to download from the [IBM Z and LinuxOne Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).

Set the enviorment variable based on the desired image version:

```
ZDLC_IMAGE=icr.io/ibmz/zdlc:5.0.0
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
ZDLC_CODE_DIR=${ZDLC_DIR}/code/credit_card_fraud_example
ZDLC_LIB_DIR=${ZDLC_DIR}/lib
ZDLC_BUILD_DIR=${ZDLC_DIR}/build
ZDLC_MODEL_DIR=${ZDLC_DIR}/models
ZDLC_DATA_DIR=${ZDLC_DIR}/data
ZDLC_MODEL_NAME=ccfd
if [ -z ${ZDLC_IMAGE} ]; then echo ERROR: ZDLC_IMAGE must be set first; fi
if [ -z ${ZDLC_DIR} ] || [ ! -d ${ZDLC_DIR} ]; then echo ERROR: ZDLC_DIR must be set to an existing zDLC example directory first; fi
```

| Variable | Description |
| -------- | ----------- |
|ZDLC_CODE_DIR=${ZDLC_DIR}/code|Used in:<br>• [Running the CCFD inference Python example](#ccfd-run)|
|ZDLC_LIB_DIR=${ZDLC_DIR}/lib|Used in:<br>• [Running the CCFD inference Python example](#ccfd-run)|
|ZDLC_MODEL_DIR=${ZDLC_DIR}/models|Used in:<br>• [Building the CCFD .so using the IBM Z Deep Learning Compiler](#so-ccfd)<br>• [Running the CCFD inference Python example](#ccfd-run)|
|ZDLC_DATA_DIR=${ZDLC_DIR}/data|Used in:<br>• [Training and Exporting a CCFD Model using PyTorch](#ccfd-build)|
|ZDLC_MODEL_NAME=ccfd|Used in:<br>• [Building the CCFD .so using the IBM Z Deep Learning Compiler](#so-ccfd)<br>• [Running the CCFD inference Python example](#ccfd-run)|
|if ... fi | Simple tests to confirm ZDLC_IMAGE and ZDLC_DIR were set. If they were not set, set them and then reset the other variables.

<br>

## Dataset used for building CCFD Model <a id="ccfd-data"></a>

The code sample in this directory uses the [Credit Card Fraud data set](https://github.com/IBM/TabFormer/tree/main/data/credit_card) and trains a model.

## Training and Exporting a CCFD Model using PyTorch <a id="ccfd-build"></a>

Creating the ONNX model that the IBM Z Deep Learning Compiler can leverage requires downloading the
[Credit Card Fraud data set](https://github.com/IBM/TabFormer/tree/main/data/credit_card) from the internet
then training the model with the `credit_card_fraud_training.py` script. This will use the Credit Card Fraud data set
and create the `ccfd.onnx` model in the ZDLC_MODEL_DIR.

Training will take some time. The epoch number in the output will indicate
progress.

### Preparing the CCFD data set

```
mkdir -p ${ZDLC_DATA_DIR}
tar -xvzf /path/to/transactions.tgz -C ${ZDLC_DATA_DIR}
```
| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| -xvzf /path/to/transactions.tgz | Compressed data set file location on local system. |
| -C ${ZDLC_DATA_DIR} | Destination of extracted .csv data set. |

### Building the IBM Z Accelerated for Pytorch container image

```
docker build -f ${ZDLC_DIR}/docker/Dockerfile.ccfd_train -t ccfd-pytorch-train-example:latest .
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker build | Build the container image. |
| -f docker/Dockerfile.ccfd_train | Use `docker/Dockerfile.ccfd_train` as the Dockerfile for this container build. |
| -t ccfd-pytorch-train-example:latest | Build the image with the `image:tag` specification of `ccfd-pytorch-train-example:latest`. |

### Training the CCFD model

```
docker run --rm -v ${ZDLC_DATA_DIR}:/data:z -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_MODEL_DIR}:/models:z ccfd-pytorch-train-example:latest /code/credit_card_fraud_training.py
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_DATA_DIR}:/data:z | The `/data` host bind mount points to the directory containing the ccfd data set. `:z` is required to share the volume if SELinux is installed. |
| -v ${ZDLC_CODE_DIR}:/code:z | The `/code` host bind mount points to the directory with the calling program. `:z` is required to share the volume if SELinux is installed. |
| -v ${ZDLC_MODEL_DIR}:/model:z | The `/model` host bind mount points to the directory with the model `.so` file. `:z` is required to share the volume if SELinux is installed. |

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

## Building the CCFD .so using the IBM Z Deep Learning Compiler <a id="so-ccfd"></a>

Use the `--EmitLib` option to build a `.so` shared library of the model specified by ZDLC_MODEL_NAME in [Environment variables](#setvars):

```
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz --maccel=NNPA ${ZDLC_MODEL_NAME}.onnx
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

The built `.so` shared library is written to the host bind mount location.

## Running the CCFD inference Python example <a id="ccfd-run"></a>

This example credit card fraud detection program is written in Python and runs using the Python Runtime. The example program calls the ONNX-MLIR Runtime APIs by leveraging [pybind and PyExecutionSession](http://onnx.ai/onnx-mlir/UsingPyRuntime.html)
which is best described in sections `Using PyRuntime` and `PyRuntime Module`
in the linked documentation.

Next, copy the PyRuntime library out of the docker container using:

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

Two configuration approaches are described in
[onnx-mlir's Configuring and using PyRuntime](http://onnx.ai/onnx-mlir/UsingPyRuntime.html),
but we'll prefer the `PYTHONPATH` approach so we avoid creating symbolic
links for this example.

Build the example Python image with the following command:

```
docker build -f ${ZDLC_DIR}/docker/Dockerfile.python -t zdlc-python-ccfd-example:latest .
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker build | Build the container image. |
| -f docker/Dockerfile.python | Use `docker/Dockerfile.python` as the Dockerfile for this container build. |
| -t zdlc-python-ccfd-example:latest | Build the image with the `image:tag` specification of `zdlc-python-ccfd-example:latest`. |

Finally, run the Python client with the following command:

```
docker run --rm -v ${ZDLC_LIB_DIR}:/build/lib:z -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_MODEL_DIR}:/models:z --env PYTHONPATH=/build/lib zdlc-python-ccfd-example:latest code/credit_card_fraud_inference.py /models/${ZDLC_MODEL_NAME}.so
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_LIB_DIR}:/build/lib:z | The `/build/lib` host bind mount points to the directory containing the PyRuntime library. `:z` is required to share the volume if SELinux is installed. |
| -v ${ZDLC_CODE_DIR}:/code:z | The `/code` host bind mount points to the directory with the calling program. `:z` is required to share the volume if SELinux is installed. |
| -v ${ZDLC_MODEL_DIR}:/model:z | The `/model` host bind mount points to the directory with the model `.so` file. `:z` is required to share the volume if SELinux is installed. |
| --env PYTHONPATH=/build/lib | When the container is launched, the `PYTHONPATH` environment variable is setup to point to `/build/lib` directory containing the PyRuntime library needed for execution. |

Once complete, you'll see output like the following:

```
Input Tensor has shape (1, 7, 220) and values:
[[[0.20302147 0.56236434 0.13909294 ... 0.10022413 0.9104976  0.9770127 ]
  [0.84120595 0.1057601  0.45215574 ... 0.7845114  0.03907652 0.98231816]
  [0.7631247  0.01472253 0.5910108  ... 0.8982474  0.6907932  0.04508637]
  ...
  [0.68221414 0.5250294  0.60738164 ... 0.15901668 0.9667138  0.22662444]
  [0.56852716 0.14096218 0.07758127 ... 0.37388662 0.87472314 0.6635935 ]
  [0.86152136 0.53854865 0.25199595 ... 0.8353012  0.79426867 0.52634805]]]
Output Tensor has shape (1, 1) and values:
[[0.9999949]]
```

Note that the output values will be random since the input values are random.
Results may vary depending on experimental setup.