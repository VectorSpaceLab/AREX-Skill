# CLAM Pipeline Overview

CLAM is a whole-slide-image workflow for weakly supervised computational pathology. It expects slide-level labels, not patch-level annotations, and trains attention-based multiple-instance-learning models on extracted patch features.

## Stage Map

| Stage | Primary route | Main CLAM surface | Inputs | Outputs |
| --- | --- | --- | --- | --- |
| WSI preprocessing | `sub-skills/wsi-preprocessing/SKILL.md` | `create_patches_fp.py`, `build_preset.py` | WSI directory, optional preset/process list | `masks/`, `patches/*.h5`, `stitches/`, `process_list_autogen.csv` |
| Feature extraction | `sub-skills/feature-extraction/SKILL.md` | `extract_features_fp.py`, `models.get_encoder` | Coordinate `.h5` files, original WSIs, slide CSV, encoder/checkpoint choice | `h5_files/*.h5`, `pt_files/*.pt` |
| Training and evaluation | `sub-skills/training-evaluation/SKILL.md` | `create_splits_seq.py`, `main.py`, `eval.py` | Dataset CSV, feature root, splits, task/model flags | checkpoints, per-fold metrics, `summary.csv`, eval CSVs |
| Heatmap visualization | `sub-skills/heatmap-visualization/SKILL.md` | `create_heatmaps.py`, heatmap YAML | Trained checkpoint, slides, config, process list | raw attention assets, production heatmap images, sampled patches |

## Working Tree Expectations

CLAM's upstream code is script-based. A user normally runs CLAM scripts from a working tree or an equivalent project layout where imports such as `models`, `utils`, `wsi_core`, `dataset_modules`, and `vis_utils` are importable. This generated skill is self-contained for agent guidance, command construction, validation, and troubleshooting; it does not bundle the full CLAM implementation or pretrained model checkpoints.

## Common Data Layouts

### Preprocessing Outputs

```text
RESULTS_DIRECTORY/
  masks/
  patches/
    slide_1.h5
  stitches/
  process_list_autogen.csv
```

The fast pipeline stores patch coordinates rather than patch image arrays. This is the preferred path for downstream feature extraction.

### Feature Outputs

```text
FEATURES_DIRECTORY/
  h5_files/
    slide_1.h5
  pt_files/
    slide_1.pt
```

Training and evaluation generally point `--data_root_dir` at a parent directory containing task-specific feature subdirectories, each with `pt_files/`.

### Dataset CSVs

Dataset CSVs need at least:

- `case_id`: patient/case identifier used to prevent leakage across splits.
- `slide_id`: slide or feature basename expected by the dataset class.
- label column: defaults to `label`, but CLAM task code can use a different `label_col` when customized.

## Encoder and Dimension Contract

| Encoder | Feature dimension | Required setup |
| --- | --- | --- |
| `resnet50_trunc` | `1024` | Default timm/torch setup |
| `uni_v1` | `1024` | `UNI_CKPT_PATH` pointing to the checkpoint file |
| `conch_v1` | `512` | CONCH package installed and `CONCH_CKPT_PATH` pointing to the checkpoint file |

Keep the same dimension in feature extraction, `main.py --embed_dim`, `eval.py --embed_dim`, and heatmap `model_arguments.embed_dim`.

## Recommended Agent Flow

1. Identify the current pipeline stage from the user's files and symptoms.
2. Read the owning sub-skill first; use sibling links only when a handoff crosses stages.
3. Run bundled helper scripts for dry command construction or config/CSV validation when the user is planning a run.
4. For heavy native commands, confirm WSIs/checkpoints/hardware/output locations before execution.
5. Record skipped heavy checks explicitly during verification or troubleshooting rather than treating dry-run success as full CLAM execution success.
