# PocketFlow Conversion Tool Reference

Read this to choose a PocketFlow export or benchmark utility after a model checkpoint exists.

## Common prerequisites

Most conversion workflows need:

- TensorFlow 1.x with `tf.contrib` and `tf.contrib.lite`.
- A model directory containing checkpoint files and a `.meta` graph file whose name ends with `model.ckpt.meta` for the main PB/TFLite exporter.
- Graph collections that identify inputs and outputs. Defaults are `images_final` and `logits_final`.
- A graph whose operations are supported by the selected conversion path.

Use the bundled artifact checker first from the `deployment-conversion` sub-skill directory:

```bash
python scripts/check_conversion_artifacts.py --model-dir models_eval
```

From this reference directory, the same helper is `../scripts/check_conversion_artifacts.py`.

## Export PB/TFLite from checkpoints

The main export workflow turns a checkpoint into a frozen PB and a TFLite model. Key flags:

| Flag | Meaning |
| --- | --- |
| `--model_dir` | Directory containing checkpoint and `.meta` files. |
| `--input_coll` | TensorFlow collection containing the model input tensor; default `images_final`. |
| `--output_coll` | TensorFlow collection containing logits/output tensor; default `logits_final`. |
| `--enbl_chn_prune` | Remove pruned input channels by graph transformation before export. |
| `--enbl_fake_prune` and `--fake_prune_ratio` | Fake pruning for speed tests only, not real compressed export. |
| `--enbl_uni_quant` | Configure quantized uint8 TFLite conversion for uniform quantization. |
| `--enbl_fake_quant` | Post-training quantization fallback; may add accuracy loss. |

Choose `--enbl_chn_prune` for channel-pruned/DCP checkpoints where zeroed channels should become cheaper operations. Choose `--enbl_uni_quant` or post-quantization flags for quantization deployment.

## Quantized export path

For `uniform-tf` checkpoints, the quantized export utility focuses on TF quantization-aware training output and post-training quantization options. Important concepts:

- `--model_dir` points to the evaluation/checkpoint directory.
- `--enbl_post_quant` can force post-training quantization when some ops were not covered by quantization-aware training.
- Mean/std/default range flags influence TFLite converter calibration assumptions.

Confirm that the model was trained or prepared for quantized export before using this path. For learner selection, read [compression-learners](../../compression-learners/SKILL.md).

## Channel-pruned export path

The channel-pruned export path detects zero input channels and replaces Conv2D inputs with gather or 1x1-conv transformations depending on data format. It needs initialized checkpoint variables and a graph layout that exposes pruned kernels.

Failure usually means the checkpoint is missing, the graph does not contain expected Conv2D ops, or data format/collection inference failed.

## Data-format conversion

The data-format conversion utility is used when checkpoint tensors or graph data format need to move between NHWC/NCHW-style expectations. Use it only when a model helper and checkpoint are known to support the conversion. Incorrect conversion can make checkpoints unusable.

## Graph collection editing

The graph collection utility adds tensors to named TensorFlow collections. It is useful when a graph lacks the default input/output collection names expected by export tools. Before editing:

- Identify tensor names from the graph.
- Decide collection names intentionally.
- Keep an untouched copy of the checkpoint/model directory.

## Inference timing

The benchmark utility times PB or TFLite inference with flags such as:

- `--model_file`
- `--input_name`
- `--output_name`
- `--input_dtype`
- `--batch_size`
- `--nb_repts_warmup`
- `--nb_repts`

Benchmark results depend on hardware, TensorFlow/TFLite runtime, batch size, and input dtype. Do not compare numbers across devices without recording those conditions.
