# D-FINE Troubleshooting

## Purpose

Read this when the task spans more than one sub-skill or when the failure is not clearly limited to data/config, training, architecture, or inference/export alone.

## Import and dependency issues

### `ModuleNotFoundError`
Common causes:

- The baseline requirements were not installed.
- An optional dependency such as `matplotlib`, `onnx`, `onnxsim`, `opencv-python`, `onnxruntime`, `tensorrt`, `openvino`, or `pycuda` is missing.
- A module defining a registered component was never imported.

Recovery:

1. Install `requirements.txt` first.
2. Add the workflow-specific optional requirements only when needed.
3. Use `scripts/dfine_environment_probe.py --repo-root . --config configs/dfine/dfine_hgnetv2_n_coco.yml --build-model` to separate a general import failure from a specific optional dependency failure.

### Source checkout import works only from one shell
If a helper fails to import `src` from a different directory, pass `--repo-root` to the bundled probe or add the checkout root to `sys.path` in your own helper.

## Config and dataset issues

- A `num_classes` mismatch usually means the config family does not match the checkpoint or dataset.
- `remap_mscoco_category` should be `False` for custom COCO-style categories unless the workflow explicitly reuses MSCOCO labels.
- `total_batch_size` must divide evenly by world size for distributed training.
- COCO JSON files must contain `images`, `annotations`, and `categories` with consistent IDs.

Use the data/config sub-skill and its validator for these failures.

## Training and checkpoint issues

- `Only support from_scrach or resume or tuning at one time` means the command mixed incompatible modes.
- `--resume` expects a full training checkpoint.
- `--tuning` is the right choice when the dataset or class count changed and you want the solver to adapt compatible head parameters.
- `ema.module` vs `model` key layout differences are normal across checkpoint styles.

Use the training/evaluation sub-skill for command generation and checkpoint selection.

## Inference and export issues

- ONNX export needs `onnx` and usually `onnxsim`.
- TensorRT workflows also need a working CUDA/TensorRT runtime and a compatible engine or `trtexec` binary.
- OpenVINO workflows need the OpenVINO runtime and an IR/XML model.
- The native inference scripts use different preprocessing strategies; a box offset is often a preprocessing mismatch rather than a model bug.

Use the inference/export sub-skill for backend-specific recovery steps.

## When to stop

Stop and ask the user when the missing piece is one of these:

- actual dataset files,
- a checkpoint,
- a GPU/backend runtime,
- a private or large download,
- or permission to run a long training/evaluation job.
