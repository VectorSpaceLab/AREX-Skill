# Conversion workflows

This reference gives safe, repository-relative workflows for checkpoint remapping and TensorFlow graph freezing. Run commands from the repository root unless a step explicitly changes directories.

## Default files and config fields

| Purpose | Default path or name | Where it is used |
|---|---|---|
| Release/original checkpoint prefix | `./checkpoint/yolov3_coco.ckpt` | `cfg.YOLO.ORIGINAL_WEIGHT`; restored by `convert_weight.py` |
| Converted/demo checkpoint prefix | `./checkpoint/yolov3_coco_demo.ckpt` | `cfg.YOLO.DEMO_WEIGHT`; saved by `convert_weight.py`, restored by `freeze_graph.py` |
| Frozen graph | `./yolov3_coco.pb` | Written by `freeze_graph.py`; consumed by image/video inference |
| Class names | `./data/classes/coco.names` by default | Loaded when `YOLOV3` builds the output heads |
| Anchors | `./data/anchors/basline_anchors.txt` by default | Loaded when `YOLOV3` decodes predictions |

A TensorFlow checkpoint prefix is not one file. A usable prefix normally has:

- `<prefix>.meta`
- `<prefix>.index`
- one or more `<prefix>.data-*` shards, commonly `<prefix>.data-00000-of-00001`

Before running conversion/freezing, use the bundled checker:

```bash
python sub-skills/conversion/scripts/check_conversion_inputs.py --repo-root .
```

Use `--strict` when a CI/preflight step should fail on missing expected artifacts.

## Flow A: release COCO checkpoint to demo checkpoint and PB

Use this when the user wants the repository's normal COCO demo model (`yolov3_coco.pb`).

1. Prepare the release checkpoint under `checkpoint/`:

   ```bash
   mkdir -p checkpoint
   cd checkpoint
   wget https://github.com/YunYang1994/tensorflow-yolov3/releases/download/v1.0/yolov3_coco.tar.gz
   tar -xvf yolov3_coco.tar.gz
   cd ..
   ```

2. Confirm the original checkpoint prefix exists:

   ```bash
   python sub-skills/conversion/scripts/check_conversion_inputs.py \
     --repo-root . \
     --original-ckpt checkpoint/yolov3_coco.ckpt
   ```

3. Convert the release checkpoint into the repository's demo checkpoint naming/layout:

   ```bash
   python convert_weight.py
   ```

   `convert_weight.py` restores `cfg.YOLO.ORIGINAL_WEIGHT` and saves `cfg.YOLO.DEMO_WEIGHT`. With the default config, that means it reads `./checkpoint/yolov3_coco.ckpt` and writes `./checkpoint/yolov3_coco_demo.ckpt`.

4. Freeze the converted checkpoint to a PB file:

   ```bash
   python freeze_graph.py
   ```

   `freeze_graph.py` restores `./checkpoint/yolov3_coco_demo.ckpt` and writes `./yolov3_coco.pb`.

5. Verify the output path before handing off to inference:

   ```bash
   python sub-skills/conversion/scripts/check_conversion_inputs.py \
     --repo-root . \
     --expect-pb
   ```

## Flow B: COCO checkpoint initialization for custom training

Use this when the user changed to a custom dataset/classes and wants to initialize the backbone and non-output layers from COCO.

1. Update the class-name config before conversion. The model graph is built using the current class file, so custom class count changes the output-head shapes.

   Typical config fields to check:

   ```python
   __C.YOLO.CLASSES = "./data/classes/<custom>.names"
   __C.YOLO.ANCHORS = "./data/anchors/basline_anchors.txt"  # or a custom 9-anchor file
   __C.TRAIN.INITIAL_WEIGHT = "./checkpoint/yolov3_coco_demo.ckpt"
   ```

2. Download/extract the original COCO checkpoint as in Flow A.
3. Run conversion with the COCO-init flag:

   ```bash
   python convert_weight.py --train_from_coco
   ```

4. What the flag changes:

   - It skips original COCO output-head variables named under `yolo-v3` with final original head names `Conv_6`, `Conv_14`, and `Conv_22`.
   - It skips current model output heads `conv_sbbox`, `conv_mbbox`, and `conv_lbbox`.
   - It saves a checkpoint at `cfg.YOLO.DEMO_WEIGHT` with compatible restored layers plus randomly initialized current heads.

5. Hand the resulting checkpoint to the training workflow, not directly to inference. A randomly initialized custom head must be trained before detections are meaningful.

## Flow C: freeze a trained or renamed checkpoint

The source `freeze_graph.py` has hard-coded values:

```python
pb_file = "./yolov3_coco.pb"
ckpt_file = "./checkpoint/yolov3_coco_demo.ckpt"
output_node_names = [
    "input/input_data",
    "pred_sbbox/concat_2",
    "pred_mbbox/concat_2",
    "pred_lbbox/concat_2",
]
```

For a custom trained checkpoint, edit a working copy or parameterize these constants so `ckpt_file` points to the desired checkpoint prefix, for example a training output such as `./checkpoint/yolov3_test_loss=9.2099.ckpt-5`. Keep `output_node_names` the same unless the graph code itself changed.

Important tensor-name distinction:

- `convert_variables_to_constants(..., output_node_names=...)` expects node names without `:0`.
- Inference fetch code normally uses tensor names with `:0`: `input/input_data:0`, `pred_sbbox/concat_2:0`, `pred_mbbox/concat_2:0`, and `pred_lbbox/concat_2:0`.

## Flow D: user asks for direct Darknet `.weights` conversion

Treat direct Darknet conversion as a patch-and-verify task, not as a ready-to-run path. The direct conversion scripts are present, but source inspection found bugs that prevent reliable use as-is. Prefer Flow A when a compatible release checkpoint is acceptable. If the user must use a Darknet `.weights` file, read the bundled troubleshooting guide first and patch a copy before execution.
