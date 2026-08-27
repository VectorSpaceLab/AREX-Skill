---
name: feature-extraction
description: "Convert CLAM patch coordinate files into feature .h5 and .pt
  artifacts with ResNet50, UNI, or CONCH encoders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Feature Extraction

Use this sub-skill when a task is about turning CLAM patch-coordinate `.h5` files into slide-level feature bags, choosing `resnet50_trunc`, `uni_v1`, or `conch_v1`, setting checkpoint environment variables, or aligning downstream `embed_dim` values with extracted features.

## Route First

- If the user still needs WSI segmentation, patch coordinates, process lists, or presets, read `../wsi-preprocessing/SKILL.md` first.
- If the user already has feature `.pt` files and is configuring splits, training, evaluation, or model checkpoints, read `../training-evaluation/SKILL.md`.
- If the user is configuring attention heatmaps or visualizing trained CLAM checkpoints, read `../heatmap-visualization/SKILL.md`.
- If the user asks why feature extraction failed, start with `references/troubleshooting.md`, then inspect the workflow or encoder reference that matches the symptom.

## Reference Map

- Read `references/workflows.md` for the fast `extract_features_fp.py` workflow, required inputs, command syntax, output layout, and downstream `data_root_dir` expectations.
- Read `references/encoder-reference.md` to choose between `resnet50_trunc`, `uni_v1`, and `conch_v1`, including checkpoint variables, feature dimensions, and batch-size implications.
- Read `references/legacy-pipeline.md` only for older saved-patch `.h5` projects that used `extract_features.py` instead of the current fast coordinate-based pipeline.
- Read `references/troubleshooting.md` to diagnose coordinate-file, `csv_path`, slide-extension, OpenSlide, checkpoint, auto-skip, batch-size, and `embed_dim` failures.
- Run `scripts/clam_feature_command_builder.py` before a heavy extraction job to validate safe CLI options and print an `extract_features_fp.py` command plus expected outputs without opening slides, loading checkpoints, or downloading weights.

## Default Workflow

1. Confirm `data_h5_dir/patches/<slide_id>.h5` exists from the fast CLAM patching workflow and contains coordinate data rather than saved image patches.
2. Confirm `csv_path` has a `slide_id` column whose values match both coordinate files and slide files after applying `--slide_ext`.
3. Pick an encoder in `references/encoder-reference.md`; set `UNI_CKPT_PATH` or `CONCH_CKPT_PATH` before using UNI or CONCH.
4. Use the bundled command builder to produce a safe command and inspect naming assumptions.
5. Run CLAM feature extraction with `extract_features_fp.py`, then point downstream training/evaluation at the parent feature root described in `references/workflows.md`.
