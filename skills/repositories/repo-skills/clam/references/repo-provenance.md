# Repository Provenance

Schema: `disco.repo-provenance.v1`

Skill id: `clam`

## Source Repository Snapshot

- Repository: CLAM
- Source kind: Git checkout
- Commit: `53e2409d4a8189c682c173382964a85f114f923c`
- Branch: `master`
- Exact tag: none detected
- Remote URL: `https://github.com/mahmoodlab/CLAM.git`
- Working tree state before generated skill artifacts: clean
- Working tree state after generation: dirty only because generated skill artifacts were added under `skills/`
- Relative generated paths: `skills/`

## Package and Runtime Baseline

- Package version: not available from distribution metadata
- Installable Python distribution metadata: none detected; CLAM is a script/source-tree project.
- Public environment evidence: `env.yml` and `docs/INSTALLATION.md`
- Documented Python family: Python 3.10 via `env.yml`
- Important runtime dependencies from repo evidence: OpenSlide, PyTorch, torchvision, timm, h5py, pandas, PyYAML, OpenCV, matplotlib, scikit-learn, scipy, tqdm, openslide-python, smooth-topk, tensorboardX.
- Optional encoder dependencies/assets: CONCH package plus `CONCH_CKPT_PATH`; UNI checkpoint plus `UNI_CKPT_PATH`.

## Evidence Paths Used

- `docs/README.md`
- `docs/INSTALLATION.md`
- `docs/README_old.md`
- `env.yml`
- `build_preset.py`
- `create_patches_fp.py`
- `create_patches.py`
- `extract_features_fp.py`
- `extract_features.py`
- `create_splits_seq.py`
- `main.py`
- `eval.py`
- `create_heatmaps.py`
- `dataset_modules/`
- `models/`
- `utils/`
- `vis_utils/`
- `wsi_core/`
- `dataset_csv/`
- `splits/`
- `presets/`
- `heatmaps/configs/config_template.yaml`
- `heatmaps/process_lists/heatmap_demo_dataset.csv`

## Refresh Guidance

Refresh this skill if CLAM changes its CLI flags, dataset schema, model constructors, encoder list, heatmap YAML schema, environment file, or recommended pipeline order. Also refresh after major upstream changes to UNI/CONCH setup or OpenSlide/torch compatibility guidance.
