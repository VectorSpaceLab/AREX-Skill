---
name: inference-and-demo
description: "Plan tf-faster-rcnn pretrained demo/image inference, checkpoint
  selection, NMS behavior, visualization, and dry-run command building without
  running the model."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tf-faster-rcnn Inference and Demo

Use this sub-skill for the repo's pretrained demo flow: choosing the backbone/dataset pair, validating the TensorFlow checkpoint prefix, reasoning about `tools/demo.py` and `lib/model/test.py`, and diagnosing inference-time image, visualization, and NMS failures.

## Route here for

- Building or explaining the stock demo command for the bundled sample images.
- Deciding between `vgg16` and `res101` for `tools/demo.py`.
- Checking the checkpoint prefix and `.meta` file before demo runs.
- Understanding the VOC class list, demo thresholds, and output window behavior.
- Debugging `cv2.imread`, `plt.show()`, or ResNet101 memory pressure during demo.

## Do not handle here

- Dataset folder creation, checkpoint downloads, or symlink layout: use `../dataset-and-assets/SKILL.md`.
- Native extension builds, `nms.gpu_nms` installation, CUDA/toolkit setup, or `USE_GPU_NMS` build recovery: use `../installation-and-configuration/SKILL.md`.
- Dataset-wide AP runs, `tools/test_net.py`, `tools/reval.py`, or training/evaluation launchers: use `../training-and-evaluation/SKILL.md`.
- Backbone internals, feature-map shapes, or custom architecture changes: use `../api-and-architecture/SKILL.md`.

## Fast path

1. Confirm the checkpoint family matches the requested network/dataset pair.
2. Validate the TensorFlow checkpoint prefix under `output/<net>/<train_imdb>/default/<snapshot>.ckpt`.
3. Remember the demo script only supports `--net {vgg16,res101}` and `--dataset {pascal_voc,pascal_voc_0712}`.
4. Use the bundled command builder to print a safe command and validation result without running inference.
5. Expect a matplotlib window after each bundled demo image; on headless systems, use an off-screen backend or save figures in a local copy of the script.

## Bundled references

- `references/demo-inference.md`: demo control flow, selectors, class labels, command shapes, and output expectations.
- `references/nms-and-postprocessing.md`: NMS dispatch, threshold handling, bbox postprocessing, and import caveats.
- `references/troubleshooting.md`: checkpoint, OpenCV, NMS, visualization, and memory failure modes.

## Bundled helper

- `scripts/demo_command_builder.py` prints a shell command for the demo script and validates the expected checkpoint files.
- It accepts `--repo-root`, `--net`, `--dataset`, `--gpu-id`, `--cpu`, and `--validate-only`.
- It never downloads assets, trains, or runs inference.

## Key facts to keep straight

- `tools/demo.py` hardcodes the five sample images under `data/demo/`.
- The demo uses the Pascal VOC class list: background plus 20 foreground labels.
- Demo thresholds are fixed in source: `CONF_THRESH = 0.8` and `NMS_THRESH = 0.3`.
- `cfg.USE_GPU_NMS=False` changes dispatch, but it does not remove the top-level `nms.gpu_nms` import in `nms_wrapper.py`.
- `lib/model/test.py` is the shared `im_detect`/`test_net` core; the demo flow is a thin wrapper around it.
