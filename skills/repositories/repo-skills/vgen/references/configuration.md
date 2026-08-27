# VGen configuration and dispatch

Use this reference when a YAML file, a `TASK_TYPE`, or a positional CLI override needs interpretation.

## Core config loader

The repository's `utils.config.Config` constructor signature is:

```text
(load=True, cfg_dict=None, cfg_level=None)
```

Observed behavior:

- It parses `--cfg`, `--init_method`, `--debug`, and trailing `opts` from the command line.
- It loads `configs/base.yaml` first when that file exists.
- It merges `_BASE`, `_BASE_RUN`, or `_BASE_MODEL` recursively when those keys are present.
- It then applies command-line override pairs.
- It exposes nested sections as `Config` objects backed by `cfg_dict`.

The typoed helper `assign_signle_cfg` is intentionally part of the repo's public runtime surface for config layering; it is used by I2VGen and DreamVideo inference to merge secondary YAMLs like `vldm_cfg`, `subject_cfg`, or `motion_cfg` before sampling.

## Registry dispatch

The root launchers are tiny:

- `train_net.py` -> `ENGINE.build(dict(type=cfg_update.TASK_TYPE), cfg_update=cfg_update.cfg_dict)`
- `inference.py` -> `INFER_ENGINE.build(dict(type=cfg_update.TASK_TYPE), cfg_update=cfg_update.cfg_dict)`

The verified task map from this checkout includes:

### Training task types

- `train_t2v_entrance`
- `train_videolcm_t2v_entrance`
- `train_dreamvideo_entrance`
- `t2v_instructvideo_entrance`

### Inference task types

- `inference_text2video_entrance`
- `inference_i2vgen_entrance`
- `inference_dreamvideo_entrance`
- `inference_instructvideo_entrance`
- `inference_higen_entrance`
- `inference_sr600_entrance`
- `inference_tft2v_entrance`
- `inference_tft2v_sr600_entrance`
- `inference_tft2v_vcomposer_entrance`
- `inference_videolcm_entrance`
- `inference_videolcm_vcomposer_entrance`

One known exception from the repo evidence: `configs/higen_train.yaml` names `train_t2v_higen_entrance`, but the current `tools/train` package does not register that trainer. Treat HiGen training as requiring a deliberate code alias or a temporary config rewrite, not as a normal dispatch target.

## Command-line override caveat

The repository's positional override pairs are useful for string paths but are not type-safe for numbers, booleans, lists, or nested dictionaries. Example:

```bash
python inference.py --cfg configs/t2v_infer.yaml test_list_path data/prompts.txt test_model models/model.pth
```

is fine because both overrides are string paths. Edits like `guide_scale 7.5`, `max_frames 32`, `double_frames_sr True`, or `partial_keys [["y","depth"]]` should be made in a copied YAML instead of on the command line.

## Common config families

- `configs/t2v_train.yaml` and `configs/t2v_infer.yaml` are the base ModelScope text-to-video pair.
- `configs/higen_train.yaml` and `configs/higen_infer.yaml` are HiGen evidence.
- `configs/videolcm_t2v_train.yaml` and `configs/videolcm_t2v_infer.yaml` are the VideoLCM train/infer pair.
- `configs/tft2v_*` and `configs/videolcm_vcomposer_*` exercise text-free or VideoComposer-style conditioning.
- `configs/i2vgen_xl_*`, `configs/dreamvideo/*`, and `configs/instructvideo/*` are specialized routes owned by their sub-skills.

## Minimal smoke guidance

Before a long run, a future agent should be able to answer all of these:

1. Which `TASK_TYPE` does the config declare?
2. Is the config intended for `train_net.py` or `inference.py`?
3. Does the config load a secondary base such as `vldm_cfg`, `subject_cfg`, or `motion_cfg`?
4. Are the paths repo-relative and present in the checkout?
5. Does the selected sub-skill own the workflow, or is it a comparison-only route?
