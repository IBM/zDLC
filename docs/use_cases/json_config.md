---
layout: default
title: JSON Configuration File
parent: Use Cases
nav_order: 8
---

# JSON Configuration File

As your NNPA tuning workflow matures, the compile command can become long and hard to reproduce. The JSON configuration file solves this: it lets you capture all compile options and per-operator NNPA decisions in a single file you can version-control, review, and share with your team.

---

## What the JSON config file does

The config file supports two independent capabilities:

1. **`compile_options`** — store your compiler flags so you never have to repeat a long `docker run` command.
2. **`nnpa_ops_config`** — control NNPA placement and quantization per individual operator node, going beyond what `--nnpa-placement-heuristic` can express.

You can use either capability alone or both together.

---

## Part 1 — Storing compile options

Create a file called `mymodel.json` in your model directory:

```json
{
  "compile_options": [
    "--EmitLib",
    "--O3",
    "-march=z17",
    "--mtriple=s390x-ibm-loz",
    "--maccel=NNPA",
    "--nnpa-quant-dynamic"
  ]
}
```

Then compile with just:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --config-file=mymodel.json \
  mymodel.onnx
```

The `compile_options` array values are applied exactly as if they were passed on the command line. Flags in `compile_options` and flags on the command line can be combined — command-line flags take precedence on conflicts.

---

## Part 2 — Per-operator device placement

The `nnpa_ops_config` section lets you override whether individual operators run on NNPA or CPU. This is more powerful than `--nnpa-placement-heuristic` because you can target specific nodes by name or shape.

### Step 1 — Get the node names from the compiler

The safest way to get correct node names (they can differ slightly from what a visualizer like Netron shows) is to have the compiler write them:

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --save-config-file=mymodel.json \
  mymodel.onnx
```

Open `mymodel.json` — it contains every operator node with its current placement decision.

### Step 2 — Override a node's device

Change `"device": "nnpa"` to `"device": "cpu"` (or vice versa) for any node you want to move:

```json
{
  "nnpa_ops_config": [
    {
      "pattern": {
        "match": {
          "node_type": "onnx.Gemm",
          "onnx_node_name": "Plus214-Times212_2"
        },
        "rewrite": {
          "device": "cpu"
        }
      }
    }
  ]
}
```

### Step 3 — Recompile

```bash
docker run --rm -v ${ZDLC_MODEL_DIR}:/workdir:z ${ZDLC_IMAGE} \
  --EmitLib --O3 -march=z17 --mtriple=s390x-ibm-loz \
  --maccel=NNPA --config-file=mymodel.json \
  mymodel.onnx
```

> **Note:** A `"device": "nnpa"` entry is a *request*, not a guarantee. The compiler still checks hardware constraints (data type, rank, tensor size). An operator that fails the legality check falls back to CPU regardless of the JSON setting.

---

## Part 3 — Selective quantization

When `--nnpa-quant-dynamic` is enabled, the compiler quantizes all eligible matmuls, which can sometimes hurt accuracy. Use `nnpa_ops_config` to selectively enable or disable quantization per operator.

The recommended approach: enable `--nnpa-quant-dynamic` globally, then use the config to turn it off for specific operators that cause accuracy regression.

### Match by node name (HuggingFace Optimum models)

HuggingFace Optimum exports structured, readable ONNX node names. You can match them with a regex:

```json
{
  "compile_options": [
    "--EmitLib", "--O3", "-march=z17",
    "--mtriple=s390x-ibm-loz",
    "--maccel=NNPA", "--nnpa-quant-dynamic"
  ],
  "nnpa_ops_config": [
    {
      "_comment": "Quantize only the self-attention output projection",
      "pattern": {
        "match": {
          "node_type": "onnx.MatMul",
          "onnx_node_name": "^/model/layers\\.[0-9]+(.*)/self_attn/o_proj/MatMul.*"
        },
        "rewrite": {
          "quantize": true
        }
      }
    },
    {
      "_comment": "Do NOT quantize the feed-forward down projection",
      "pattern": {
        "match": {
          "node_type": "onnx.MatMul",
          "onnx_node_name": "^/model/layers\\.[0-9]+(.*)/mlp/down_proj/MatMul.*"
        },
        "rewrite": {
          "quantize": false
        }
      }
    }
  ]
}
```

### Match by tensor shape (torch_onnxmlir / auto-generated names)

Models exported via `torch.onnx.export` often have cryptic auto-generated node names like `MatMul_283`. In this case, match by the input tensor shape instead:

```json
{
  "compile_options": [
    "--EmitLib", "--O3", "-march=z17",
    "--mtriple=s390x-ibm-loz",
    "--maccel=NNPA", "--nnpa-quant-dynamic"
  ],
  "nnpa_ops_config": [
    {
      "_comment": "Do NOT quantize the down_proj MatMul — shape [?,?,4096]*[4096,2048]",
      "pattern": {
        "match": {
          "node_type": "onnx.MatMul",
          "inputs": {
            "0": {
              "dims": {
                "-1": "4096"
              }
            },
            "1": {
              "rank": "2",
              "dims": {
                "0": "4096",
                "1": "2048"
              }
            }
          }
        },
        "rewrite": {
          "quantize": false
        }
      }
    }
  ]
}
```

In the `dims` object, the key is the dimension index (with `-1` meaning the last dimension) and the value is the expected size as a string.

---

## Recommended workflow

1. **Start simple:** compile with `--maccel=NNPA` only and measure baseline accuracy and throughput.
2. **Add quantization:** add `--nnpa-quant-dynamic` and re-measure. Check if accuracy is acceptable.
3. **If accuracy regressed:** run `--save-config-file` to get node names and shapes. Add `nnpa_ops_config` entries to disable quantization for the operators most likely to cause error.
4. **Iterate:** disable quantization for one layer group at a time until accuracy recovers.
5. **Lock in the config:** store the final JSON in your repository alongside the model. Compile from the config file going forward.

---

## Complete example config

```json
{
  "compile_options": [
    "--EmitLib",
    "--O3",
    "-march=z17",
    "--mtriple=s390x-ibm-loz",
    "--maccel=NNPA",
    "--nnpa-quant-dynamic",
    "--nnpa-placement-heuristic=FasterOpsWSU"
  ],
  "nnpa_ops_config": [
    {
      "_comment": "Keep the final classification head on CPU for accuracy",
      "pattern": {
        "match": {
          "node_type": "onnx.Gemm",
          "onnx_node_name": "classifier/MatMul"
        },
        "rewrite": {
          "device": "cpu",
          "quantize": false
        }
      }
    }
  ]
}
```

---

## Reference

| Key | Purpose |
|---|---|
| `compile_options` | Array of compiler flags — same as command-line arguments |
| `nnpa_ops_config` | Array of per-operator match/rewrite rules |
| `pattern.match.node_type` | ONNX operator type, e.g. `"onnx.MatMul"` |
| `pattern.match.onnx_node_name` | Node name or regex — use `--save-config-file` to get exact names |
| `pattern.match.inputs` | Match by tensor shape — useful when node names are auto-generated |
| `pattern.rewrite.device` | `"nnpa"` or `"cpu"` — device placement override |
| `pattern.rewrite.quantize` | `true` or `false` — selective quantization control |

| Flag | Purpose |
|---|---|
| `--save-config-file=<path>` | Write current placement decisions to JSON |
| `--config-file=<path>` | Load placement/quantization decisions from JSON |

For the complete schema, see the [ONNX-MLIR JSON config documentation](https://github.com/onnx/onnx-mlir/blob/0.5.1.0/docs/JsonConfigFile-NNPA.md).

See [Compiler Options — NNPA](../compiler_options_nnpa.html) for flag descriptions.
