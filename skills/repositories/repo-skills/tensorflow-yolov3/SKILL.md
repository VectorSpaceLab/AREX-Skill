---
name: tensorflow-yolov3
description: "Guides legacy TensorFlow 1.x YOLOv3 workflows for data
  preparation, checkpoint conversion, frozen-graph inference, training, and
  Pascal VOC mAP evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# tensorflow-yolov3

Use this repo skill when a task mentions **YunYang1994/tensorflow-yolov3**, TensorFlow 1.x YOLOv3, `core.yolov3.YOLOV3`, `yolov3_coco.pb`, COCO checkpoint conversion, VOC annotation lists, `train.py`, `evaluate.py`, or the bundled `mAP` workflow.

This is a legacy script-style repository, not an installable Python package. Most source scripts assume they are run from a YOLOv3 working directory where relative paths like `./data/classes/coco.names`, `./data/anchors/basline_anchors.txt`, `./checkpoint/...`, and `./mAP/...` exist.

## Start here

1. Read [repository provenance](references/repo-provenance.md) before deciding whether this skill is current for a checkout.
2. Read [environment notes](references/environment.md) before installing dependencies or debugging TensorFlow import failures.
3. Run the bundled environment checker from the runtime skill root when a user has a local working copy:

   ```bash
   python scripts/check_environment.py --repo-root <repo-root>
   ```

4. Route the user request to the narrowest sub-skill below.

## Sub-skill routes

- [data-preparation](sub-skills/data-preparation/SKILL.md): class files, anchors, annotation text rows, Pascal VOC conversion, and dataset-input validation before training or evaluation.
- [conversion](sub-skills/conversion/SKILL.md): release COCO checkpoint remapping, `--train_from_coco`, freezing `yolov3_coco.pb`, output tensor names, and known Darknet conversion script bugs.
- [inference](sub-skills/inference/SKILL.md): frozen `.pb` image/video/camera inference, tensor contract checks, preprocessing, postprocessing, NMS, and empty-detection troubleshooting.
- [training](sub-skills/training/SKILL.md): `core/config.py` training fields, `Dataset`, two-stage training, logs/checkpoints, COCO initialization, and long-run/GPU/data risk checks.
- [evaluation](sub-skills/evaluation/SKILL.md): `evaluate.py`, generated `mAP/ground-truth` and `mAP/predicted` files, Pascal VOC AP/mAP formats, and isolated mAP fixture checks.

## Shared references

- [architecture](references/architecture.md): Darknet-53/YOLOv3 graph structure, config defaults, verified tensor shapes, and helper APIs shared across sub-skills.
- [environment](references/environment.md): dependency/version guidance for TensorFlow 1.x, Python, protobuf, OpenCV/Pillow, and headless systems.
- [troubleshooting](references/troubleshooting.md): cross-cutting install, relative-path, missing-weight, missing-data, and legacy GPU issues.

## Minimal import and graph sanity check

For a local working copy, use a TensorFlow 1.x-capable environment and run from the working copy root:

```bash
python - <<'PY'
import tensorflow as tf
from core.yolov3 import YOLOV3

tf.reset_default_graph()
input_data = tf.placeholder(dtype=tf.float32, shape=(1, 416, 416, 3), name='input_data')
model = YOLOV3(input_data, trainable=False)
print(model.pred_sbbox.shape.as_list())  # [1, 52, 52, 3, 85] for COCO classes
print(model.pred_mbbox.shape.as_list())  # [1, 26, 26, 3, 85]
print(model.pred_lbbox.shape.as_list())  # [1, 13, 13, 3, 85]
PY
```

If that import fails before the graph is built, read [environment](references/environment.md) and [troubleshooting](references/troubleshooting.md) first. A common cause is importing `core.utils` outside a working directory where `./data/classes/coco.names` exists.

## Do not overclaim verification

The checkout used for this skill did not include full checkpoint shards, a frozen PB, or complete VOC image datasets. The generated guidance was verified with source inspection, TensorFlow 1.x CPU graph construction, and safe helper/script checks. Full training, real inference, and checkpoint conversion still require user-supplied model/data artifacts and a compatible TensorFlow 1.x runtime.
