---
layout: default
title: C++ and Java Inference
parent: Use Cases
nav_order: 5
---

# Use Case: C++ and Java Inference

This guide walks through building and running C++ and Java applications that call IBM zDLC-compiled models. Both languages use the ONNX-MLIR runtime APIs built into the compiled `.so` or `.jar` file.

**Prerequisites:** Complete [Getting Started](../getting_started.html) first and have your environment variables set, including `ZDLC_BUILD_DIR`, `ZDLC_MODEL_DIR`, `ZDLC_CODE_DIR`, `GCC_IMAGE_ID`, and `JDK_IMAGE_ID`.

---

## C++ inference

### Step 1 — Compile the model to a `.so`

```bash
docker run --rm \
  -v ${ZDLC_MODEL_DIR}:/workdir:z \
  ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  ${ZDLC_MODEL_NAME}.onnx
```

### Step 2 — Copy the ONNX-MLIR runtime API headers and libraries

These files are needed to compile your C++ program against the runtime API:

```bash
mkdir -p ${ZDLC_BUILD_DIR}
docker run --rm \
  -v ${ZDLC_BUILD_DIR}:/files:z \
  --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} \
  -c "cp -r /usr/local/{include,lib} /files"
```

Optionally verify the files were copied:

```bash
ls -laR ${ZDLC_BUILD_DIR}
```

### Step 3 — Pull the GCC container

```bash
docker pull ${GCC_IMAGE_ID}
```

### Step 4 — Compile the C++ program

Copy the compiled model `.so` into the code directory, then build:

```bash
cp ${ZDLC_MODEL_DIR}/${ZDLC_MODEL_NAME}.so ${ZDLC_CODE_DIR}

docker run --rm \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_BUILD_DIR}:/build:z \
  ${GCC_IMAGE_ID} \
  g++ -std=c++11 -O3 \
  -I /build/include \
  /code/deep_learning_compiler_run_model_example.cpp \
  -l:${ZDLC_MODEL_NAME}.so -L/code \
  -Wl,-rpath='$ORIGIN' \
  -o /code/deep_learning_compiler_run_model_example
```

| Flag | Description |
|---|---|
| `-std=c++11 -O3` | C++ standard and optimization level. |
| `-I /build/include` | Location of the ONNX-MLIR runtime header files. |
| `-l:${ZDLC_MODEL_NAME}.so` | Link against the compiled model shared library. |
| `-L/code` | Tell the linker where to find the model `.so`. |
| `-Wl,-rpath='$ORIGIN'` | **Important:** tells the GNU loader to find the model `.so` at runtime relative to the executable's location. Without this the program will fail to load the model at runtime. |
| `-o /code/deep_learning_compiler_run_model_example` | Output executable name. |

### Step 5 — Run the C++ program

```bash
docker run --rm \
  -v ${ZDLC_CODE_DIR}:/code:z \
  ${GCC_IMAGE_ID} \
  /code/deep_learning_compiler_run_model_example
```

The program runs inference with randomly generated input values. The expected output is a list of random float values from the model.

Source code: [`code/deep_learning_compiler_run_model_example.cpp`](https://github.com/IBM/zDLC/blob/main/code/deep_learning_compiler_run_model_example.cpp)

---

## Java inference

### Step 1 — Compile the model to a `.jar`

```bash
docker run --rm \
  -v ${ZDLC_MODEL_DIR}:/workdir:z \
  ${ZDLC_IMAGE} \
  --EmitJNI --O3 -march=z17 --mtriple=s390x-ibm-loz \
  ${ZDLC_MODEL_NAME}.onnx
```

### Step 2 — Copy the ONNX-MLIR runtime libraries

```bash
mkdir -p ${ZDLC_BUILD_DIR}
docker run --rm \
  -v ${ZDLC_BUILD_DIR}:/files:z \
  --entrypoint '/usr/bin/bash' ${ZDLC_IMAGE} \
  -c "cp -r /usr/local/{include,lib} /files"
```

### Step 3 — Pull the JDK container

```bash
docker pull ${JDK_IMAGE_ID}
```

### Step 4 — Compile the Java program

```bash
mkdir -p ${ZDLC_CODE_DIR}/class

docker run --rm \
  -v ${ZDLC_CODE_DIR}:/code:z \
  -v ${ZDLC_BUILD_DIR}:/build:z \
  ${JDK_IMAGE_ID} \
  javac \
  -classpath /build/lib/javaruntime.jar \
  -d /code/class \
  /code/deep_learning_compiler_run_model_example.java
```

| Flag | Description |
|---|---|
| `-classpath /build/lib/javaruntime.jar` | Required path to the IBM ONNX-MLIR Java runtime jar. |
| `-d /code/class` | Output directory for compiled `.class` files. |

### Step 5 — Run the Java program

Copy the compiled model `.jar` into the code directory, then run:

```bash
cp ${ZDLC_MODEL_DIR}/${ZDLC_MODEL_NAME}.jar ${ZDLC_CODE_DIR}

docker run --rm \
  -v ${ZDLC_CODE_DIR}:/code:z \
  ${JDK_IMAGE_ID} \
  java \
  -classpath /code/class:/code/${ZDLC_MODEL_NAME}.jar \
  deep_learning_compiler_run_model_example
```

> **Note:** The `classpath` shown uses paths as they appear inside the container (via bind mounts). If running the Java program directly on the host outside of Docker, adjust the `classpath` to point to the actual host paths.

The program runs inference with randomly generated input values. The expected output is a list of random float values from the model.

Source code: [`code/deep_learning_compiler_run_model_example.java`](https://github.com/IBM/zDLC/blob/main/code/deep_learning_compiler_run_model_example.java)
