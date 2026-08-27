# VGen overview

VGen is a config-driven video synthesis codebase. Future agents should treat it as a collection of related CUDA video-generation workflows, not as a normal importable Python package with a stable public API.

## Workflow families

| Family | Use this sub-skill | Natural task signals |
| --- | --- | --- |
| ModelScope T2V, HiGen, TF-T2V, VideoLCM, VideoComposer-style conditioning, SR600 | `sub-skills/text-to-video/` | text-to-video, prompt list, `t2v_infer.yaml`, `higen`, `tft2v`, `videolcm`, `vcomposer`, `sr600`, train/inference config dispatch |
| I2VGen-XL | `sub-skills/image-to-video/` | image-to-video, `i2vgen_xl_infer.yaml`, image plus caption list, Gradio demo, Cog predictor, person I2VGen config |
| DreamVideo | `sub-skills/dreamvideo/` | subject customization, motion customization, joint subject+motion generation, adapters, DreamVideo metrics |
| InstructVideo | `sub-skills/instructvideo/` | reward fine-tuning, HPSv2, LoRA reward training, InstructVideo eval presets, WebVid reward lists |

## Common operating pattern

1. Identify the target config and read `TASK_TYPE`.
2. Use the matching sub-skill to understand required data, checkpoint, and backend assumptions.
3. Validate list files before GPU work.
4. Dry-run the dispatcher or workflow-specific wrapper.
5. Launch only after model checkpoints and CUDA runtime are available.
6. Use copied YAML files for typed edits; keep positional CLI overrides for string path fields.

## Shared bundled helpers

Run helper paths from this generated skill root unless a command says otherwise.

- `scripts/check_runtime.py` checks imports, CUDA, ffmpeg, and the heavy `tools` registration import.
- `scripts/dispatch_config.py` adapts the repo's `train_net.py` and `inference.py` config dispatch into one dry-runnable wrapper.
- `scripts/inspect_list_file.py` validates prompt, path-caption, prompt-or-seed, and DreamVideo metric list formats.
- `scripts/dump_unet_key_sets.py` forwards to the DreamVideo adapter-key helper for shared temporal/spatial UNet key exports.

## Scope boundaries

Include the repo's own `README.MD`, `doc/`, `configs/`, `data/`, `tools/`, `utils/`, `metric/`, and `test_func/` evidence. Exclude generated skill/test artifacts, model checkpoints, large downloaded data, caches, and third-party vendored metric code except as provenance for the metric wrapper.

Demo wrappers such as `gradio_app.py` and `predict.py` are useful evidence, but they are not the required offline path because they rely on network-backed ModelScope/Cog/Gradio deployment dependencies.
