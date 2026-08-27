# Troubleshooting

## Install and import issues

- If `av` tries to build from source or complains about FFmpeg libraries, install the video runtime first. A working fix is to ensure `av` and `ffmpeg` are available before the full requirements install.
- If `pip check` flags `decord` as unsupported on the current platform, treat the PyAV/FFmpeg path as the supported video path and keep going with the rest of the skill.
- If `deepspeed` import fails because it cannot find `CUDA_HOME` or `nvcc`, the host does not have a usable CUDA toolkit for extension checks. That is a runtime-toolchain problem, not a model-code problem.
- If `gradio` is missing, only the serving route is blocked; other workflows still work.

## Model and flag issues

- `Qwen3.5` should normally use `--disable_flash_attn2 True` in this repo.
- `--enable_reasoning True` on unsupported model families should be treated as a validation error, not a warning.
- `fps` and `nframes` must not both be set for video datasets.
- QLoRA should not be combined with vision training knobs that keep the vision tower trainable.
- If you enable LoRA for classification, remember that the classifier head uses `modules_to_save` and should not be stacked under a LoRA wrapper.

## Data issues

- Missing `image_folder` or `eval_image_folder` usually means relative image/video paths cannot be resolved.
- DPO samples must supply both `chosen_reasoning` and `rejected_reasoning` or neither.
- Qwen3-VL Thinking requires reasoning on every assistant turn when reasoning is enabled.
- Classification labels must map to the repo’s expected integer classes.

## Runtime issues

- The repo’s inference and merge paths are asset-heavy. Use dry-run or help checks first.
- If a CUDA library error mentions `libcudnn_cnn_train.so.8` or a similar symbol mismatch, the README’s workaround is to unset `LD_LIBRARY_PATH`.
- Use ZeRO-2 or CPU offload templates when memory pressure is the main obstacle, not when the actual model behavior needs to be preserved for verification.
