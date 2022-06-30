# Using the IBM Z Deep Learning Compiler Container Images

## Table of contents
* [Overview](#overview)
* [Download the IBM Z Deep Learning compiler container image](#container)
* [IBM Z Deep Learning Compiler command line interface help](#cli-help)
* [Building the code samples](#code-samples)
    * [Building a model .so using the IBM Z Deep Learning Compiler](#build-so)
    * [Building C++ programs to call the model](#run-cpp)
    * [Building a model .jar file using the IBM zDLC compiler](#build-jar)
    * [Building Java programs to call the model](#run-java)
    * [Running the Python example](#run-python)
* [IBM Z Integrated Accelerator for AI](#nnpa-overview)
    * [Compiling models to utilize the IBM Z Integrated Accelerator for AI](#nnpa-compile)
    * [ONNX Operators that support the IBM Z Integrated Accelerator for AI](#nnpa-ops)
* [Deleting the container image](#del-image)

## Overview <a id="overview"></a>
The IBM Z Deep Learning Compiler uses [ONNX-MLIR](http://onnx.ai/onnx-mlir/) to
compile .onnx deep learning AI models into shared libaries. The shared libaries
can then be integrated into C, C++, Java, or Python applications.

The compiled models take advantage of IBM zSystems technologies including SIMD
on IBM z13 and later and the Integrated Accelerator for AI available on IBM z16
without changes to the original model.

ONNX is an open format for representing AI models. It is open source and vendor
neutral. Some AI frameworks directly support exporting to .onnx format. For
other frameworks, open source converters are readily available. [ONNX Support Tools](
https://onnx.ai/supported-tools.html) has links to steps and converters for many
popular AI frameworks.

See [Verfied ONNX Model Zoo models](models/README.md#verified-models)
for the list of models from the [ONNX Model Zoo](https://github.com/onnx/models)
that have been built and verified with the IBM Z Deep Learning Compiler.

These are the general end-to-end steps to use IBM zDLC:
1. Create, convert, or download an ONNX model.
1. Download the onnx-mlir image from [IBM Z and LinuxOne Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).
1. Use the image to compile a shared library of the model for your desired language.
1. Import the compiled model into your application.
1. Run your application.

## Download the IBM Z Deep Learning Compiler container image <a id="container"></a>

Downloading the IBM Z Deep Learning Compiler container image requires
credentials for the `icr.io` registry. Information on obtaining the credentials
is located at [IBM Z and LinuxONE Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).

You can pull the image as shown in the following code block:

```
ZDLC_IMAGE_ID=icr.io/ibmz/onnx-mlir:[version]
docker pull ${ZDLC_IMAGE_ID}
```
Set `[version]` based on the version available in IBM Z and
LinuxONE Container Registry. We will use this environment variable to simplify
the container commands throughout the rest of this document.


## IBM Z Deep Learning Compiler command line interface help <a id="cli-help"></a>

Running the IBM Z Deep Learning Compiler container image with no parameters
shows the complete help for the IBM Z Deep Learning Compiler.

```
docker run --rm ${ZDLC_IMAGE_ID}
```

Note the command line entry point for the IBM Z Deep Learning Compiler is the
`onnx-mlir` command. The IBM Z Deep Learning Compiler is invoked by running the
`onnx-mlir` image with the `docker run` command.

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |

The help for the IBM Z Deep Learning Compiler can also be displayed by
adding the `--help` option to the command line.

## Building the code samples <a id="code-samples"></a>
The easiest way to follow the examples is to clone the example code repository:

```
git clone https://github.com/IBM/zDLC
```

The code examples are located in the GitHub repository. After the `git clone`,
set these environment variables on the command line.

```
ZDLC_DIR=$(pwd)/zDLC
ZDLC_MODEL_DIR=${ZDLC_DIR}/models
ZDLC_CODE_DIR=${ZDLC_DIR}/code
```

The code examples build three deep learning models from the ONNX Model Zoo. See
[Obtaining the models](models/README.md#obtain-models) to download the models
used in the examples.

### Building a model .so using the IBM Z Deep Learning Compiler <a id="build-so"></a>
Use the `--EmitLib` option to build a `.so` shared library of the mnist-8 model:

```
ZDLC_MODEL_NAME=mnist-8
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE_ID} --EmitLib --O3 --mcpu=z14 --mtriple=s390x-ibm-loz ${ZDLC_MODEL_NAME}.onnx
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| ZDLC_MODEL_NAME=mnist-8 | Name of the model to compile without ending suffix. |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_MODEL_DIR}:/workdir:z | The host bind mount points to the directory with the model ONNX file. `:z` is required to share the volume if SELinux is installed. |
| --EmitLib | Build the `.so` shared library of the model. |
| --O3 | Optimize to the highest level. |
| --mcpu=z14 | The minimum CPU architecture (for generated code instructions). |
| --mtriple=s390x-ibm-loz | The target architecture for generated code. |
| ${ZDLC_MODEL_NAME}.onnx | Builds the `.so` shared library from the specified ONNX file. |

The built `.so` shared library is written to the host bind mount location.

The ONNX models for the examples can be found in the [ONNX Model Zoo](https://github.com/onnx/models).

### Building C++ programs to call the model <a id="run-cpp"></a>

The example program is written in the C++ programming language and compiled
with the `g++` compiler. The example program calls the IBM Z Deep Learning
Compiler APIs built into the `.so` shared library. The source code for the
example program is at
[C++ example](code/deep_learning_compiler_run_model_example.cpp).

Some setup steps are required before building the programs to call
the model. The ONNX-MLIR Runtime API files first need to be copied
from the container image. Run these commands from the command line
to copy files.

```
ZDLC_BUILD_DIR=${ZDLC_DIR}/build
mkdir -p ${ZDLC_BUILD_DIR}
docker run --rm -v ${ZDLC_BUILD_DIR}:/files:z --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE_ID} -c "cp -r /usr/local/{include,lib} /files"
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_BUILD_DIR}:/files:z | The host bind mount points to the directory to copy the build files from IBM. `:z` is required to share the volume if SELinux is installed. |
| cp | Run the copy command to copy the build files from IBM into the host bind mount. |

Run this optional step to see the files that were copied.

```
ls -laR ${ZDLC_BUILD_DIR}
```

Next pull a Docker image with the `g++` compiler tools installed.

```
GCC_IMAGE_ID=icr.io/ibmz/gcc:12
docker pull ${GCC_IMAGE_ID}
```

The setup steps have been completed. Use the `g++` image and the
ONNX-MLIR C++ Runtime API files to build the program.

```
cp ${ZDLC_MODEL_DIR}/${ZDLC_MODEL_NAME}.so ${ZDLC_CODE_DIR}
docker run --rm -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_BUILD_DIR}:/build:z ${GCC_IMAGE_ID} g++ -std=c++11 -O3 -I /build/include /code/deep_learning_compiler_run_model_example.cpp -l:${ZDLC_MODEL_NAME}.so -L/code -Wl,-rpath='$ORIGIN' -o /code/deep_learning_compiler_run_model_example
```

The following table explains the command line:

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_CODE_DIR}:/code:z | The `/code` host bind mount points to the directory with the calling program. `:z` is required to share the volume if SELinux is installed. |
| -v ${ZDLC_BUILD_DIR}:/build:z | The `/build` host bind mount points to the directory containing the build files from IBM. `:z` is required to share the volume if SELinux is installed. |

The following table explains the `g++` command line:

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| g++ | Run the g++ compiler from the container command line. |
| -std=c++11 -O3 | `g++` compiler options (See the `man g++` help for additional information.). |
| -I /build/include | This is the location of the include header files. |
| /code/deep_learning_compiler_run_model_example.cpp | The example program to build. |
| -l:${ZDLC_MODEL_NAME}.so | The model `.so` shared library that was previously built. |
| -L/code | Tell the `g++` linker where to find the model `.so` shared library. |
| -Wl,-rpath='$ORIGIN' | (This is a very important parameter for correctly building the C++ example program.) The GNU loader (LD) uses the `rpath` to locate the model `.so` file when the program is run. (See the `man ld.so` help for additional information.) |
| -o /code/deep_learning_compiler_run_model_example | Tell the `g++` linker the name of the built program. |

The program is now ready to be run from the command line. When run, the program
will inference the model with randomly generated test data values.

```
docker run --rm -v ${ZDLC_CODE_DIR}:/code:z ${GCC_IMAGE_ID} /code/deep_learning_compiler_run_model_example
```

With this example, the program is linked to the built model and is run
in the container. The expected program output is ten random float values
(because the input was random) from the MNIST model.

### Building a model .jar file using the IBM zDLC compiler <a id="build-jar"></a>

Use the `--EmitJNI` option to build a jar file of the model. This example is
for the resnet50-caffe2-v1-8 ONNX model:

```
ZDLC_MODEL_NAME=resnet50-caffe2-v1-8
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE_ID} --EmitJNI --O3 --mcpu=z14 --mtriple=s390x-ibm-loz ${ZDLC_MODEL_NAME}.onnx
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| ZDLC_MODEL_NAME=resnet50-caffe2-v1-8 | Name of the model to compile without ending suffix. |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_MODEL_DIR}:/workdir:z | The host bind mount points to the directory with the model ONNX file. `:z` is required to share the volume if SELinux is installed. |
| --EmitJNI | Build the jar file of the model. |
| ${ZDLC_MODEL_NAME}.onnx | Builds the `.jar` shared library from the specified ONNX file.|

The built jar file is written to the host bind mount location.

### Building Java programs to call the model <a id="run-java"></a>

The example program is written in the Java programming language and compiled
with a Java JDK. The example program calls the ONNX-MLIR Java Runtime APIs
through the JNI interfaces built in the model jar file. The source code
for the example program is at
[Java example](code/deep_learning_compiler_run_model_example.java).

Some setup steps are required before building the programs to call
the model. The ONNX-MLIR Runtime API files first need to be copied
from the container image. Run these commands from the command line
to copy files.

```
ZDLC_BUILD_DIR=${ZDLC_DIR}/build
mkdir -p ${ZDLC_BUILD_DIR}
docker run --rm -v ${ZDLC_BUILD_DIR}:/files:z --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE_ID} -c "cp -r /usr/local/{include,lib} /files"
```
| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_BUILD_DIR}:/files:z | The host bind mount points to the directory to copy the build files from IBM. `:z` is required to share the volume if SELinux is installed. |
| cp | Run the copy command to copy the build files from IBM into the host bind mount. |

Run this optional step to see the files that were copied.

```
ls -laR ${ZDLC_BUILD_DIR}
```

Pull a Java JDK image to build and run the Java example:

```
JDK_IMAGE_ID=icr.io/ibmz/openjdk:11
docker pull ${JDK_IMAGE_ID}
```

Build the Java calling program using the `javac` command.

```
mkdir -p ${ZDLC_CODE_DIR}/class
docker run --rm -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_BUILD_DIR}:/build:z ${JDK_IMAGE_ID} javac -classpath /build/lib/javaruntime.jar -d /code/class /code/deep_learning_compiler_run_model_example.java
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_CODE_DIR}:/code:z | The `/code` host bind mount points to the directory with the calling program. `:z` is required to share the volume if SELinux is installed. |
| -v ${ZDLC_BUILD_DIR}:/build:z | The `/build` host bind mount points to the directory containing the build files from IBM. `:z` is required to share the volume if SELinux is installed. |
| javac | Run the JDK Java compiler from the container command line. |
| -classpath /build/lib/javaruntime.jar | Need to specify the path to the run-time jar from IBM. |
| -d /code/class | The build class files are stored at ${ZDLC_CODE_DIR}/class. |

The program is now ready to be run from the command line. When run, the program
will inference the model with randomly generated test data values.

```
cp ${ZDLC_MODEL_DIR}/${ZDLC_MODEL_NAME}.jar ${ZDLC_CODE_DIR}
docker run --rm -v ${ZDLC_CODE_DIR}:/code:z ${JDK_IMAGE_ID} java -classpath /code/class:/code/${ZDLC_MODEL_NAME}.jar deep_learning_compiler_run_model_example
```

With this example, the Java `classpath` contains the paths for the host
bind mounts when run within the container. The `classpath` needs to be
adjusted if the Java program is run directly from the command line. The
expected program output is a list of float values from the RESNET50 model.

### Running the Python example <a id="run-python"></a>

This example program is written in Python and runs using the Python runtime.
The example program calls the ONNX-MLIR Runtime APIs by leveraging
[pybind and PyExecutionSession](http://onnx.ai/onnx-mlir/UsingPyRuntime.html)
which is best described in sections `Using PyRuntime` and `PyRuntime Module`
in the linked documentation.

To start, obtain `mobilenetv2-7.onnx` following the
[models instructions](models/README.md).

Once complete, compile `mobilenetv2-7` to a [.so shared library](#build-so)
as described previously by replacing `mnist-8.onnx` with `mobilenetv2-7.onnx`.

Next, copy the PyRuntime library out of the docker container using:

```
ZDLC_LIB_DIR=${ZDLC_DIR}/lib
mkdir -p ${ZDLC_LIB_DIR}
docker run --rm -v ${ZDLC_LIB_DIR}:/files:z --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE_ID} -c "cp /usr/local/lib/PyRuntime.cpython-*-s390x-linux-gnu.so /files"
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
docker build -f ${ZDLC_DIR}/docker/Dockerfile.python -t zdlc-python-example .
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| docker build | Build the container image. |
| -f docker/Dockerfile.python | Use `docker/Dockerfile.python` as the Dockerfile for this container build. |
| -t zdlc-python-example | Build the image with the `image:tag` specification of `zdlc-python-example:latest`. |

Finally, run the Python client with the following command:

```
ZDLC_MODEL_DIR=${ZDLC_DIR}/models
ZDLC_CODE_DIR=${ZDLC_DIR}/code
```
```
docker run --rm -v ${ZDLC_LIB_DIR}:/build/lib:z -v ${ZDLC_CODE_DIR}:/code:z -v ${ZDLC_MODEL_DIR}:/models:z --env PYTHONPATH=/build/lib zdlc-python-example:latest /code/deep_learning_compiler_run_model_python.py /models/${ZDLC_MODEL_NAME}.so
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
The input tensor dimensions are:
[1, 3, 224, 224]
A brief overview of the output tensor is:
[[-2.4883294   0.4591511   1.1298141  ... -2.8113475  -1.3842212
   2.6721394 ]
 [-5.064701    0.17290297 -1.866698   ...  0.39307398 -4.6048536
   2.116905  ]
 [-3.6744304   1.906144   -2.4807017  ... -0.96054727 -3.919518
   0.92789984]]
The dimensions of the output tensor are:
(3, 1000)
```
Note that the output values will be random since the input values are random.

## IBM Z Integrated Accelerator for AI <a id="nnpa-overview"></a>
IBM z16 systems include a new Integrated Accelerator for AI to enable real-time
AI for transaction processing at scale. The IBM Z Deep Learning Compiler helps
your new and existing deep learning models take advantage of this new
accelerator.

Any IBM zSystem can be used to compile models to take advantage of the
Integrated Accelerator for AI, including IBM z15 and older machines. However, if
acceleration is enabled at compile time, the compiled model will only run on
IBM zSystems which have the accelerator. Machines which have an accelerator
can run models compiled without acceleration but those models will not take
advantage of the accelerator.

### Compiling models to utilize the IBM Z Integrated Accelerator for AI <a id="nnpa-compile"></a>

Like other compilers, the IBM zDLC's default settings compile models so that
they run on as many systems as possible. To use machine specific features,
such as the Integrated Accelerator for AI, you must specify an additional option
when compiling the model.

When set, supported ONNX Operators are directed to
the accelerator instead of the CPU. The compile process handles routing
the operations between the CPU and accelerator and any required data conversion.
No changes are required to your model.

To compile a model to use the Integrated Accelerator for AI, The `--maccel=NNPA`
option needs to be specified on the command line.
Additionally, since the accelerator is only available for IBM z16 and greater,
it is recommended to also use `--mcpu=16`.

Using the [`.so shared library example`](#build-so), the command line to compile
models that take advantage of the Integrated Accelerator for AI is:

```
ZDLC_MODEL_NAME=mnist-8
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE_ID} --EmitLib --O3 --mcpu=z16 --mtriple=s390x-ibm-loz --maccel=NNPA ${ZDLC_MODEL_NAME}.onnx
```

Once the model is built to use the IBM Z Integrated Accelerator for AI,
no changes are required on the command line to run the model:

```
cp ${ZDLC_MODEL_DIR}/${ZDLC_MODEL_NAME}.so ${ZDLC_CODE_DIR}
docker run --rm -v ${ZDLC_CODE_DIR}:/code:z ${GCC_IMAGE_ID} /code/deep_learning_compiler_run_model_example
```

The same flags are required for compiling shared libraries for any language
including Java and Python. Likewise, no additional steps are required when
running the shared libraries.

### ONNX Operators that support the IBM Z Integrated Accelerator for AI <a id="nnpa-ops"></a>
When compiled to use the Integrated Accelerator for AI, the following ONNX
Operators use the accelerator. Other ONNX Operators use CPU.

* Add
* AveragePool
* BatchNormalization
* Conv
* Div
* Exp
* Gemm
* GlobalAveragePool
* GRU - must use tanh activation. Otherwise CPU is used.
* Log
* LogSoftmax
* LSTM - must use tanh activation. Otherwise CPU is used.
* MatMul
* Max
* MaxPool
* Min
* Mul
* ReduceMean
* Relu
* Sigmoid
* Softmax
* Sub
* Sum
* Tanh

## Deleting the container image <a id="del-image"></a>

First, find the `IMAGE ID` for the container image.

```
docker images
```

Then delete the image using the `IMAGE ID`.

```
docker rmi IMAGE-ID
```

If an in-use error occurs while attempting to delete the container image,
use the `docker ps -a` command to show any running containers. Use the
`docker stop` and `docker rm` commands to remove the running instances
of the container. Then re-run the `docker rmi` command.
