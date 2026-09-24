---
layout: default
title: Scope and Versioning
nav_order: 7
---


# Scope and Versioning Policy

## Project scope

IBM Z Deep Learning Compiler (IBM zDLC) follows a continuous release model with a cadence of 3–4 minor releases per year. Bug fixes are applied to the next minor release and are not back-ported to earlier releases.

Each release of IBM zDLC links to a specific version of ONNX-MLIR and supports CPU and the IBM Z Integrated AI Accelerator (NNPA) on IBM Z systems. Other ONNX-MLIR accelerators are not supported.

### Supported ONNX operations

| Target | Reference |
|---|---|
| CPU | [Supported ONNX Operations for CPU](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-cpu.md) |
| IBM Z Integrated Accelerator (NNPA) | [Supported ONNX Operations for NNPA](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/SupportedONNXOps-NNPA.md) |

Operations not listed in these tables, or usage that falls outside documented limitations, are beyond IBM zDLC project scope.

---

## Versioning

IBM zDLC follows [semantic versioning](https://semver.org/) with a few compiler-specific deviations. Each release is versioned as `[MAJOR].[MINOR].[PATCH]`.

### MAJOR

All releases sharing the same major number have runtime APIs that are **forward compatible**. A program built against model libraries from `X.0` will run model libraries compiled by any later `X.Y` release.

A major version bump indicates one or more of:
- Runtime API changes that are incompatible with earlier releases (programs that import model libraries may need updating).
- Critical compile-time flag changes incompatible with earlier releases.
- Significant feature additions beyond a normal minor release.

> Note: Pre-built PyRuntime binaries for Python versions that have reached end-of-life may be removed without a major version bump.

### MINOR

Minor releases contain new features, improvements, and bug fixes. IBM zDLC strives to keep minor releases fully compatible with earlier releases, but performance, debug, or accelerator-specific compile-time flags may change in incompatible ways. Support for end-of-life language runtimes may also be removed in minor releases.

### PATCH

Patch releases contain only bug fixes, security updates, or updates to non-IBM zDLC packages bundled in the container. Only compatible changes are introduced in patch releases.
