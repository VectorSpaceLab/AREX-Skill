# CLAM Troubleshooting

Use this reference for failures that cut across multiple CLAM stages. For workflow-specific symptoms, route to the nearest sub-skill troubleshooting file.

## Install and Import Problems

CLAM is a source-tree script project rather than a normal installable package. If imports such as `models`, `utils`, `dataset_modules`, `wsi_core`, or `vis_utils` fail:

- Run CLAM scripts from the working tree root or set the equivalent project root on `PYTHONPATH`.
- Confirm the environment follows the documented Python 3.10-style dependency stack.
- Confirm OpenSlide is installed at both the native library level and the `openslide-python` level.
- Avoid mixing incompatible NumPy/SciPy/scikit-learn/PyTorch binaries when repairing environments.

## OpenSlide and WSI Read Failures

Symptoms include import failures for `openslide`, unsupported slide formats, or crashes when opening `.svs`, `.ndpi`, `.tiff`, or similar files.

- Verify native OpenSlide libraries are installed before retrying CLAM preprocessing, feature extraction, or heatmaps.
- Confirm slide paths and `--slide_ext` match actual filenames.
- Check whether the files are valid whole-slide images rather than ordinary TIFF/PNG/JPEG images.
- For very large slides, review segmentation level choices in `sub-skills/wsi-preprocessing/references/troubleshooting.md`.

## Optional Encoder Failures

`resnet50_trunc` is the default. UNI and CONCH need extra assets:

- `uni_v1`: set `UNI_CKPT_PATH` to a valid UNI checkpoint file before feature extraction or heatmap runs.
- `conch_v1`: install the CONCH package and set `CONCH_CKPT_PATH` to a valid CONCH checkpoint file.
- Do not expect the generated skill to provide or download restricted model weights; users must obtain them according to the upstream model instructions.
- Match feature dimensions: ResNet50/UNI use `1024`, CONCH uses `512`.

## Data Layout Mismatches

Common cross-stage problems:

- Patch coordinate `.h5` files belong under `data_h5_dir/patches/` for `extract_features_fp.py`.
- Feature extraction writes both `h5_files/` and `pt_files/`; training expects `.pt` feature tensors in task-specific feature directories.
- Dataset CSV `slide_id` values must match feature basenames and should be consistent with slide filenames used during feature extraction.
- `case_id` should group slides from the same patient/case to prevent leakage across splits.

## GPU, Memory, and Runtime Limits

CLAM can run parser/help and many validation checks on CPU, but real feature extraction, training, evaluation, and heatmap generation may need GPU memory and long runtimes.

- Reduce `--batch_size` for feature extraction when CUDA memory is low.
- Use the same `--embed_dim` or heatmap `model_arguments.embed_dim` as the feature encoder output.
- Confirm checkpoints were trained with the same `model_type`, `model_size`, `drop_out`, `n_classes`, and feature dimension used at evaluation or heatmap time.
- Treat WSI processing, full feature extraction, training, and heatmaps as heavy native runs; use dry-run helpers before launching them.

## Script Working Directory Problems

Many upstream CLAM scripts assume repository-relative files such as `dataset_csv/`, `splits/`, `presets/`, and `heatmaps/configs/`.

- Run upstream scripts from a CLAM working tree or adjust paths intentionally.
- When using bundled skill helpers, run them from the generated skill/sub-skill directory or pass absolute paths to user data/configs.
- The bundled helpers do not run CLAM itself; they validate options, render commands, and document expected outputs.

## Where to Continue

- WSI mask, preset, skip, and patch-coordinate issues: `sub-skills/wsi-preprocessing/references/troubleshooting.md`.
- Encoder, coordinate `.h5`, output feature, and feature dimension issues: `sub-skills/feature-extraction/references/troubleshooting.md`.
- Dataset CSV, split, task, training, evaluation, checkpoint, and metric issues: `sub-skills/training-evaluation/references/troubleshooting.md`.
- Heatmap YAML, ROI, process-list, checkpoint visualization, and rendering issues: `sub-skills/heatmap-visualization/references/troubleshooting.md`.
