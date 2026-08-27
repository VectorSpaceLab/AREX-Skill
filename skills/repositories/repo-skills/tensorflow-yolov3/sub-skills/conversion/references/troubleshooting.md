# Conversion troubleshooting

Use this guide before rerunning expensive TensorFlow restores, freezing, or direct Darknet conversion. All paths below are repository-relative examples.

## Missing checkpoint artifacts

Symptoms:

- `DataLossError`, `NotFoundError`, or `Failed to find any matching files for ./checkpoint/yolov3_coco.ckpt`
- `convert_weight.py` prints no variables or fails while restoring `cfg.YOLO.ORIGINAL_WEIGHT`
- `freeze_graph.py` fails while restoring `./checkpoint/yolov3_coco_demo.ckpt`

Checks:

```bash
python sub-skills/conversion/scripts/check_conversion_inputs.py --repo-root . --strict
```

Expected checkpoint files for prefix `./checkpoint/yolov3_coco.ckpt`:

- `./checkpoint/yolov3_coco.ckpt.meta`
- `./checkpoint/yolov3_coco.ckpt.index`
- `./checkpoint/yolov3_coco.ckpt.data-00000-of-00001` or another `.data-*` shard

Remedies:

- Extract the release tarball inside `checkpoint/`, not one directory above or below it.
- Pass checkpoint prefixes without `.meta`, `.index`, or `.data-*` suffixes when editing scripts.
- Treat `checkpoint/checkpoint` as a TensorFlow state hint, not proof that every shard exists.

## Variable count or shape mismatch in `convert_weight.py`

Symptoms:

- `RuntimeError` after variable counts differ.
- `RuntimeError` after `cur_shape != org_shape`.
- Failure happens after changing `cfg.YOLO.CLASSES` or class-name files.

Cause and remedies:

- Plain `python convert_weight.py` expects the current graph head shapes to match the original COCO graph. It is appropriate for the default 80-class COCO setup.
- For a custom number of classes, use `python convert_weight.py --train_from_coco`. This skips output heads in both the original checkpoint and current graph, then saves randomly initialized current heads.
- Update `cfg.YOLO.CLASSES` before running `--train_from_coco`; the current graph is built using that class file.
- If mismatch continues with `--train_from_coco`, check whether the architecture, anchor-per-scale value, variable naming, or TensorFlow graph code changed. The skip lists only cover the expected output heads: `conv_sbbox`, `conv_mbbox`, `conv_lbbox` and original `Conv_6`, `Conv_14`, `Conv_22`.

## `freeze_graph.py` restores the wrong checkpoint

Symptoms:

- Restore failure for `./checkpoint/yolov3_coco_demo.ckpt` even though another training checkpoint exists.
- Frozen graph is still named `yolov3_coco.pb` when a custom name was expected.

Cause:

`freeze_graph.py` hard-codes:

```python
pb_file = "./yolov3_coco.pb"
ckpt_file = "./checkpoint/yolov3_coco_demo.ckpt"
```

Remedies:

- Edit a working copy of `freeze_graph.py` or parameterize those constants for the intended checkpoint prefix and PB output path.
- If freezing a custom-class checkpoint, ensure `cfg.YOLO.CLASSES` points to the same class file used when the checkpoint was created.
- Keep output node names unchanged unless the graph code itself changed.

## Frozen PB exists but inference cannot fetch tensors

Symptoms:

- Tensor lookup errors for prediction or input names.
- Confusion between node names and tensor names.

Use these names when freezing:

```text
input/input_data
pred_sbbox/concat_2
pred_mbbox/concat_2
pred_lbbox/concat_2
```

Use these names when fetching tensors for inference:

```text
input/input_data:0
pred_sbbox/concat_2:0
pred_mbbox/concat_2:0
pred_lbbox/concat_2:0
```

Do not add `:0` to `output_node_names` passed to `convert_variables_to_constants`.

## Custom PB gives empty or nonsensical detections

Likely causes:

- The checkpoint was produced by `--train_from_coco` but custom output heads were not trained yet.
- The inference class-name file does not match the checkpoint's class count/order.
- The anchor file differs from the one used for training.
- Score/IoU thresholds in the inference workflow hide low-confidence boxes.

Remedies:

- Train the custom heads before expecting meaningful inference.
- Keep class-name order stable across conversion, training, freezing, and inference.
- Reuse the same 18-number anchor file or regenerate/train consistently.

## Direct Darknet conversion scripts are not reliable as-is

The direct `.weights` scripts are useful evidence, but do not run them unmodified in a production workflow.

Known `from_darknet_weights_to_ckpt.py` issues:

- The placeholder assignment for `darknet_weights` is syntactically invalid: it contains a broken quoted string around the example path.
- `load_weights()` uses `np.fromfile`, `np.prod`, and `np.transpose` but the file does not import `numpy as np`.
- The variable name `iput_size` is misspelled. It is used consistently in the placeholder shape, so it is mostly a readability issue, but patch it in any maintained copy.

Known `from_darknet_weights_to_pb.py` issues:

- It imports `load_weights` from the broken checkpoint converter, so it inherits that script's failures.
- It writes to `output_graph`, which is undefined; the intended variable is `pb_file`.
- It should be rechecked after patching to confirm the same output node names are exported.

Safe response to a user requesting Darknet conversion:

1. Warn that the bundled direct conversion scripts are broken as shipped.
2. Prefer the release checkpoint conversion flow if acceptable.
3. If direct `.weights` import is required, patch a copy, add a safe input checker for the `.weights` file, run syntax checks, then run conversion in a disposable working directory.

## TensorFlow/protobuf compatibility

Symptoms:

- TensorFlow 1.x import fails with protobuf descriptor errors.
- GPU TensorFlow 1.11 wheels are unavailable or incompatible with modern CUDA hardware.

Remedies:

- Use a Python 3.7-era TensorFlow 1.15.x CPU environment for conversion/freezing when GPU acceleration is not required.
- Pin protobuf to `3.20.x` if TensorFlow 1.x fails with modern protobuf.
- Do not make legacy GPU setup a prerequisite for simple checkpoint conversion unless the user explicitly requires GPU execution.
