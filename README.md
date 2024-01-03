# Using the IBM Z Deep Learning Compiler Container Images

## Table of contents
* [Overview](#overview)
* [Download the IBM Z Deep Learning Compiler container image](#container)
* [Environment variables](#setvars)
* [IBM Z Deep Learning Compiler command line interface help](#cli-help)
* [Building the code samples](#code-samples)
    * [Building a model .so using the IBM Z Deep Learning Compiler](#build-so)
    * [Building C++ programs to call the model](#run-cpp)
    * [Building a model .jar file using the IBM zDLC](#build-jar)
    * [Building Java programs to call the model](#run-java)
    * [Running the Python example](#run-python)
* [IBM Z Integrated Accelerator for AI](#nnpa-overview)
    * [Compiling models to utilize the IBM Z Integrated Accelerator for AI](#nnpa-compile)
    * [Performance tips for IBM Z Integrated Accelerator for AI](#nnpa-tips)
        * [Specifying input tensor dimensions](#nnpa-tips-shape)
        * [View operation targets at compile time](#nnpa-tips-ops-target)
* [Obtaining IBM Z Deep Learning Compiler debug instrumentation](#inst-debug)
* [Scope and Versioning](#scope-and-versioning)
    * [Project Scope](#scope)
        * [Supported ONNX Operations for CPU](#cpu-ops)
        * [Supported ONNX Operation for IBM Z Integrated Accelerator (NNPA)](#nnpa-ops)
    * [Versioning Policy](#versioning)
* [Removing IBM Z Deep Learning Compiler](#del-image)
<br>

# Overview <a id="overview"></a>

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
1. Download the zdlc image from [IBM Z and LinuxOne Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).
1. Use the image to compile a shared library of the model for your desired language.
1. Import the compiled model into your application.
1. Run your application.
<br>

## Download the IBM Z Deep Learning Compiler container image <a id="container"></a>

Downloading the IBM Z Deep Learning Compiler container image requires
credentials for the `icr.io` registry. Information on obtaining the credentials
is located at [IBM Z and LinuxONE Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).
<br>

Determine the desired version of the zdlc image to download from the [IBM Z and LinuxOne Container Registry](https://ibm.github.io/ibm-z-oss-hub/main/main.html).


Set ZDLC_IMAGE based on the desired IBM zDLC version:

```
ZDLC_IMAGE=icr.io/ibmz/zdlc:4.1.1
```
<br>

Pull the image as shown:

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

## Environment variables <a id="setvars"></a>

Set the environment variables for use with the IBM Z Deep Learning Compiler
container image. The environment variables will simplify the container commands
throughout the rest of this document. See the description in the table below for
additional information.

NOTE: ZDLC_IMAGE and ZDLC_DIR are based on your local system. To set these
environment variables, see:
* [Download the IBM Z Deep Learning Compiler container image](#container)
* [Download the IBM Z Deep Learning Compiler example repository](#clone_examples)


```
GCC_IMAGE_ID=icr.io/ibmz/gcc:12
JDK_IMAGE_ID=icr.io/ibmz/openjdk:11
ZDLC_CODE_DIR=${ZDLC_DIR}/code
ZDLC_LIB_DIR=${ZDLC_DIR}/lib
ZDLC_BUILD_DIR=${ZDLC_DIR}/build
ZDLC_MODEL_DIR=${ZDLC_DIR}/models
ZDLC_MODEL_NAME=mnist-12
if [ -z ${ZDLC_IMAGE} ]; then echo ERROR: ZDLC_IMAGE must be set first; fi
if [ -z ${ZDLC_DIR} ] || [ ! -d ${ZDLC_DIR} ]; then echo ERROR: ZDLC_DIR must be set to an existing zDLC example directory first; fi
```

| Variable | Description |
| -------- | ----------- |
|GCC_IMAGE_ID=icr.io/ibmz/gcc:12|Used in:<br>• [Building C++ programs to call the model](#run-cpp)<br>• [Compiling models to utilize the IBM Z Integrated Accelerator for AI](#nnpa-compile)|
|JDK_IMAGE_ID=icr.io/ibmz/openjdk:11|Used in:<br>• [Building Java programs to call the model](#run-java)|
|ZDLC_CODE_DIR=${ZDLC_DIR}/code|Used in:<br>• [Building C++ programs to call the model](#run-cpp)<br>• [Building Java programs to call the model](#run-java)<br>• [Running the Python example](#run-python)<br>• [Compiling models to utilize the IBM Z Integrated Accelerator for AI](#nnpa-compile)|
|ZDLC_LIB_DIR=${ZDLC_DIR}/lib|Used in:<br>• [Running the Python example](#run-python)|
|ZDLC_BUILD_DIR=${ZDLC_DIR}/build|Used in:<br>• [Building C++ programs to call the model](#run-cpp)<br>• [Building Java programs to call the model](#run-java)|
|ZDLC_MODEL_DIR=${ZDLC_DIR}/models|Used in:<br>• [Building the code samples](#code-samples)<br>• [Building a model .so using the IBM Z Deep Learning Compiler](#build-so)<br>• [Building C++ programs to call the model](#run-cpp)<br>• [Building a model .jar file using the IBM zDLC](#build-jar)<br>• [Building Java programs to call the model](#run-java)<br>• [Running the Python example](#run-python)<br>• [Compiling models to utilize the IBM Z Integrated Accelerator for AI](#nnpa-compile)<br>• [Obtaining IBM Z Deep Learning Compiler debug instrumentation](#inst-debug)|
|ZDLC_MODEL_NAME=mnist-12|Used in:<br>• [Building the code samples](#code-samples)<br>• [Building a model .so using the IBM Z Deep Learning Compiler](#build-so)<br>• [Building C++ programs to call the model](#run-cpp)<br>• [Compiling models to utilize the IBM Z Integrated Accelerator for AI](#nnpa-compile)<br>• [Building a model .jar file using the IBM zDLC](#build-jar)<br>• [Building Java programs to call the model](#run-java)<br>• [Running the Python example](#run-python)<br>• [Obtaining IBM Z Deep Learning Compiler debug instrumentation](#inst-debug)|
|if ... fi | Simple tests to confirm ZDLC_IMAGE and ZDLC_DIR were set. If they were not set, set them and then reset the other variables.
<br>

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

# Building the code samples <a id="code-samples"></a>


If you are using the default mnist example model from the ONNX Model Zoo,
you can download it using:
```
wget --directory-prefix $ZDLC_MODEL_DIR https://github.com/onnx/models/raw/main/validated/vision/classification/mnist/model/$ZDLC_MODEL_NAME.onnx
```
<br>

or see [Obtaining the models](models/README.md#obtain-models) to download the other models from
the model zoo. The examples use $ZDLC_MODEL_DIR as the directory and $ZDLC_MODEL_NAME specifies
the model name (without the .onnx) in that directory.

<br>

## Building a model .so using the IBM Z Deep Learning Compiler <a id="build-so"></a>

Use the `--EmitLib` option to build a `.so` shared library of the model specified by ZDLC_MODEL_NAME in [Environment variables](#setvars):

```
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitLib --O3 --mcpu=z14 --mtriple=s390x-ibm-loz ${ZDLC_MODEL_NAME}.onnx
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| ZDLC_MODEL_NAME | Name of the model to compile without ending suffix. |
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

<br>

## Building C++ programs to call the model <a id="run-cpp"></a>

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
mkdir -p ${ZDLC_BUILD_DIR}
docker run --rm -v ${ZDLC_BUILD_DIR}:/files:z --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} -c "cp -r /usr/local/{include,lib} /files"
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
(because the input was random) from the model.

### Building a model .jar file using the IBM zDLC compiler <a id="build-jar"></a>

Use the `--EmitJNI` option to build a jar file of the model specified by ZDLC_MODEL_NAME in [Environment variables](#setvars).

```
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitJNI --O3 --mcpu=z14 --mtriple=s390x-ibm-loz ${ZDLC_MODEL_NAME}.onnx
```

| Command<br>and<br>Parameters | Description |
| ----------- | -------------------------------------------------------- |
| ZDLC_MODEL_NAME | Name of the model to compile without ending suffix. |
| docker run | Run the container image. |
| --rm | Delete the container after running the command. |
| -v ${ZDLC_MODEL_DIR}:/workdir:z | The host bind mount points to the directory with the model ONNX file. `:z` is required to share the volume if SELinux is installed. |
| --EmitJNI | Build the jar file of the model. |
| ${ZDLC_MODEL_NAME}.onnx | Builds the `.jar` shared library from the specified ONNX file.|

The built jar file is written to the host bind mount location.

<br>

## Building Java programs to call the model <a id="run-java"></a>

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
mkdir -p ${ZDLC_BUILD_DIR}
docker run --rm -v ${ZDLC_BUILD_DIR}:/files:z --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} -c "cp -r /usr/local/{include,lib} /files"
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
expected program output is a list of random float values (because the
input was random) from the model.

<br>

## Running the Python example <a id="run-python"></a>

This example program is written in Python and runs using the Python runtime.
The example program calls the ONNX-MLIR Runtime APIs by leveraging
[pybind and PyExecutionSession](http://onnx.ai/onnx-mlir/UsingPyRuntime.html)
which is best described in sections `Using PyRuntime` and `PyRuntime Module`
in the linked documentation.

If not already compiled, compile the model specified by ZDLC_MODEL_NAME in [Environment variables](#setvars) to a [.so shared library](#build-so)
as described previously.

Next, copy the PyRuntime library out of the docker container using:

```
mkdir -p ${ZDLC_LIB_DIR}
docker run --rm -v ${ZDLC_LIB_DIR}:/files:z --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} -c "cp /usr/local/lib/PyRuntime.cpython-*-s390x-linux-gnu.so /files"
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

<br>

# IBM Z Integrated Accelerator for AI <a id="nnpa-overview"></a>

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

<br>

## Compiling models to utilize the IBM Z Integrated Accelerator for AI <a id="nnpa-compile"></a>

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
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitLib --O3 --mcpu=z16 --mtriple=s390x-ibm-loz --maccel=NNPA ${ZDLC_MODEL_NAME}.onnx
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

<br>

## Performance tips for IBM Z Integrated Accelerator for AI <a id="nnpa-tips"></a>

When compiling models for the IBM Z Integrated Accelerator for AI, IBM zDLC
optimizes models to take advantage of the accelerator when possible. In order to
support a wide range of models, IBM zDLC will compile models so operators not
supported by the accelerator, or operators with unsupported settings, run
on the CPU.

<br>

### Specifying input tensor dimensions <a id="nnpa-tips-shape"></a>

When running models with multiple dynamic dimensions (i.e. models with
multiple `-1` in their input signatures), using the `--shapeInformation` flag
to set those dimensions to static values may improve model runtime performance.
For some models, this allows the IBM zDLC to better determine at compile time
which operations will be compatible with the accelerator.

For example, if a vision model has an input tensor with shape `(-1, -1, -1, 3)`
representing `(batch, height, width, channels)`, you may see increased
performance by specifying the `height` and `width` dimensions at compile time.
To do so, add `--shapeInformation 0:-1x640x480x3` when compiling the model.
If the model has mutliple input tensors, those can also be specified using
`--shapeInformation 0:-1x640x480x3,1:-1x100,2:... `.

The `--shapeInformation` flag can be used with `--onnx-op-stats` to determine
if specifying the shape enables more operations to run on the IBM Z Integrated
Accelerator for AI. See [View operation targets at compile time](#nnpa-tips-ops-target).

<br>

### View operation targets at compile time<a id="nnpa-tips-ops-target"></a>

The IBM Z Deep Learning Compiler can optionally report the number of Operators
that will run on CPU vs the IBM Z Integrated Accelerator for AI at compile time.

When compiling the model, add `--onnx-op-stats [TXT|JSON]`. Operations that
begin with `onnx.*` will execute on CPU and operations that begin with `zhigh.*`
are related to the IBM Z Integrated Accelerator for AI.

<br>

# Scope and Versioning Policy <a id="scope-and-versioning"></a>

## Project Scope <a id="scope"></a>
IBM Z Deep Learning Compiler (IBM zDLC) follows a continuous release model with
a cadence of 3-4 minor releases per year. Bug fixes are applied to the next
minor release and are not ported to earlier major or minor releases.

Each release of IBM zDLC links to a specific version of ONNX-MLIR and supports
CPU and IBM Z integrated AI Accelerator (NNPA) on IBM Z systems. Other
ONNX-MLIR accelerators are not supported by IBM zDLC.

The following links lists supported operators, operator opset ranges, and any
operator specific limitations. Operators that are not listed or usage of
documented limitations are beyond IBM zDLC project scope:
* [Supported ONNX Operation for CPU](https://github.com/onnx/onnx-mlir/blob/v0.4.1.2/docs/SupportedONNXOps-cpu.md) <a id="cpu-ops"></a>
* [Supported ONNX Operation for IBM Z Integrated Accelerator (NNPA)](https://github.com/onnx/onnx-mlir/blob/v0.4.1.2/docs/SupportedONNXOps-NNPA.md) <a id="nnpa-ops"></a>


## Versioning Policy <a id="versioning"></a>

IBM Z Deep Learning Compiler (IBM zDLC) follows the
[semantic versioning guidelines](https://semver.org/) with a few deviations.
These differences account for IBM zDLC’s nature as a compiler and are outlined
below. Each zDLC release is versioned as: `[MAJOR].[MINOR].[PATCH]`

### MAJOR / VERSION:

All releases with the same major number have runtime APIs that are compatible
with earlier releases. That means programs designed to run model libraries
generated by IBM zDLC `X.0` will be able to run model libraries generated by
later IBM zDLC releases that have the same major version, (i.e. `X.0`, `X.1`,
`X.2`, etc.). Programs designed to run model libraries generated by IBM zDLC
`X.1` are able to run model libraries generated by IBM zDLC `X.1`, `X.2`, etc.

Changes in major releases indicate one or more of the following:
* Changes related to runtime APIs that are incompatible with earlier releases.
Programs that import model libraries generated by IBM zDLC might need to be
updated between major releases depending on the affected runtime API languages.

* Changes related to critical or general model compile time flags that are
incompatible with earlier releases.

* Significant feature additions beyond normal minor release updates.

Note: Prebuilt pybind11 PyRuntimes for versions of Python that have reached
end of life can be removed without a major release increase change.

### MINOR / FEATURE:

Minor releases typically contain new features, improvements, and bug fixes.

Generally, we strive to keep minor releases fully compatible with earlier
releases. However, there may be cases where performance, debug, or accelerator
specific compile time flags can be changed in incompatible ways during minor
releases.

Support for end-of-life languages may be removed in minor releases.

### PATCH / MAINTENANCE:

Patch releases contain only bug fixes, security updates or updates to non-IBM
zDLC packages included in the IBM zDLC containers. IBM zDLC only introduces
compatible changes in patch updates.

<br>

# Obtaining IBM Z Deep Learning Compiler debug instrumentation <a id="inst-debug"></a>

Instrumention debug information can be obtained during model runtime using two different methods during model compilation for the IBM Z Deep Learning Compiler.
1. [Profile IR option](#profile-ir)
2. [Instrument options](#instrument-options)

<br>

## Profile IR Option<a id="profile-ir"></a>

Spcifying the `--profile-ir` option for the IBM Z Deep Learning Compiler to cause instrumention debug information to be printed during model runtime.

The values for the `--profile-ir` option are as follows:

  |Option Value|Description|
  |-----------|--------------------------------------------------------|
  |None|No profiling. This is the defualt.|
  |Onnx|Profile for onnx ops.|
  |ZHigh|Profile for NNPA zhigh ops.|

### Examples

1. Profiling for onnx ops:

   Compiling the model:
   ```
   docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitLib --O3 --mcpu=z16 --mtriple=s390x-ibm-loz --maccel=NNPA --profile-ir=Onnx ${ZDLC_MODEL_NAME}.onnx
   ```
   Sample output when running model:
   ```
   #0) before onnx.Constant Time elapsed: 1692618036.154512 accumulated: 1692618036.154512 (Times212_reshape1)
   #1) after  onnx.Constant Time elapsed: 0.000005 accumulated: 1692618036.154517 (Times212_reshape1)
   #2) before onnx.Constant Time elapsed: 0.000002 accumulated: 1692618036.154519 (Plus112-Convolution110-Initializer_Parameter88)
   #3) after  onnx.Constant Time elapsed: 0.000004 accumulated: 1692618036.154523 (Plus112-Convolution110-Initializer_Parameter88)
   ```
2. Profiling for zhigh ops:

   Compiling the model:
   ```
   docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitLib --O3 --mcpu=z16 --mtriple=s390x-ibm-loz --maccel=NNPA --profile-ir=ZHigh ${ZDLC_MODEL_NAME}.onnx
   ```
   Sample output when running model:
   ```
   #8) before zhigh.StickifiedConstant Time elapsed: 0.000003 accumulated: 1692617935.010772 (ReLU32-Plus30-Convolution28-Initializer_Parameter6)
   #9) after  zhigh.StickifiedConstant Time elapsed: 0.000004 accumulated: 1692617935.010776 (ReLU32-Plus30-Convolution28-Initializer_Parameter6)
   #10) before zhigh.Conv2D Time elapsed: 0.000003 accumulated: 1692617935.010779 (ReLU32-Plus30-Convolution28-Initializer_Parameter6)
   #11) after  zhigh.Conv2D Time elapsed: 0.000161 accumulated: 1692617935.010940 (ReLU32-Plus30-Convolution28-Initializer_Parameter6)
   ```

 Notes:
  * The call to initialize instrumentation, OMInstrumentInit, must be done before loading the model shared library.
  * Runtime instrumenting will affect model performance due to the additional tracking and printing.

<br>

## Instrument Options <a id="instrument-options"></a>

Spcifying the instrument options for the IBM Z Deep Learning Compiler to cause instrumention debug information to be printed during model runtime.

There are three types of instrument options that can be specified.

1. The stage to be instrumented is specified using the `--instrument-stage` option with value:

      |Option Value|Description|
      |-----------|--------------------------------------------------------|
      |Onnx|Get onnx-level profiling. If "--maccel=NNPA" is also specified then get profile onnx ops before lowering to zhigh.|
      |ZHigh|Get NNPA profiling for onnx and zhigh ops.|
      |ZLow|Get NNPA profiling for zlow ops.|

2. The operations to be instrumented are specified using the `--instrument-ops` option with value:

      |Option Value|Description|
      |-----------|--------------------------------------------------------|
      |NONE or ""|No instrumentation.|
      |ops1,ops2, ...|Multiple ops.  e.g. onnx.Conv,onnx.Add for Conv and Add ops.|
      |ops.*|Ops using * wildcard. e.g. onnx.* for all onnx operations.|

3. The instrumentation actions are specified using the following options:

      |Option|Description|
      |-----------|--------------------------------------------------------|
      |`--InstrumentBeforeOp`|Insert instrument before op.|
      |`--InstrumentAfterOp`|Insert instrument after op.|
      |`--InstrumentReportTime`|Instrument runtime reports time usage.|
      |`--InstrumentReportMemory`|Instrument runtime reports memory usage.|

### Examples

1. Profiling time for onnx ops before lowering to zhigh ops:

   Compiling the model:
   ```
   docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitLib --O3 --mcpu=z16 --mtriple=s390x-ibm-loz --maccel=NNPA --instrument-stage=Onnx --instrument-ops=onnx.* --InstrumentBeforeOp --InstrumentAfterOp --InstrumentReportTime ${ZDLC_MODEL_NAME}.onnx
   ```
   Sample output when running model:
   ```
   #  0) before onnx.Constant Time elapsed: 1691688479.493696 accumulated: 1691688479.493696
   #  1) after  onnx.Constant Time elapsed: 0.000005 accumulated: 1691688479.493701
   #  2) before onnx.Constant Time elapsed: 0.000004 accumulated: 1691688479.493705
   #  3) after  onnx.Constant Time elapsed: 0.000004 accumulated: 1691688479.493709
   ```

2. Profiling time for onnx and zhigh ops:

   Compiling the model:
   ```
   docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitLib --O3 --mcpu=z16 --mtriple=s390x-ibm-loz --maccel=NNPA --instrument-stage=ZHigh --instrument-ops=onnx.*,zhigh.* --InstrumentBeforeOp --InstrumentAfterOp --InstrumentReportTime ${ZDLC_MODEL_NAME}.onnx
   ```
   Sample output when running model:
   ```
   # 24) before onnx.Reshape Time elapsed: 0.000002 accumulated: 1691688806.270982 (Times212_reshape0)
   # 25) after  onnx.Reshape Time elapsed: 0.000001 accumulated: 1691688806.270983 (Times212_reshape0)
   # 26) before zhigh.Stick Time elapsed: 0.000002 accumulated: 1691688806.270985
   # 27) after  zhigh.Stick Time elapsed: 0.000003 accumulated: 1691688806.270988
   ```

3. Profiling memory for zlow ops:

   Compiling the model:
   ```
   docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} --EmitLib --O3 --mcpu=z16 --mtriple=s390x-ibm-loz --maccel=NNPA --instrument-stage=ZLow --instrument-ops=zlow.* --InstrumentBeforeOp --InstrumentAfterOp --InstrumentReportMemory ${ZDLC_MODEL_NAME}.onnx
   ```
   Sample output when running model:
   ```
   # 14) before zlow.matmul VMem:  5456
   # 15) after  zlow.matmul VMem:  5456
   # 16) before zlow.add VMem:  5456
   # 17) after  zlow.add VMem:  5456
   ```

 Notes:
  * The call to initialize instrumentation, OMInstrumentInit, must be done before loading the model shared library.
  * Runtime instrumenting will affect model performance due to the additional tracking and printing.

<br>

# Removing IBM Z Deep Learning Compiler <a id="del-image"></a>

<br>

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
