---
name: clam
description: "Use CLAM for weakly supervised computational pathology workflows
  on whole-slide images, from WSI patching through features, training,
  evaluation, and heatmaps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# CLAM

Use this repo skill when a task involves CLAM: data-efficient, weakly supervised computational pathology on whole-slide images with slide-level labels. CLAM workflows usually move from WSI segmentation and patch coordinates, to feature extraction, to CLAM/MIL training and evaluation, and finally to attention heatmap visualization.

## Route First

- For raw WSIs, tissue masks, patch-coordinate `.h5` files, stitched QC images, process lists, or segmentation presets, read `sub-skills/wsi-preprocessing/SKILL.md`.
- For ResNet50, UNI, or CONCH feature extraction into `h5_files/` and `pt_files/`, read `sub-skills/feature-extraction/SKILL.md`.
- For dataset CSVs, train/validation/test splits, `main.py`, `eval.py`, CLAM_SB/CLAM_MB/MIL choices, checkpoints, or metrics, read `sub-skills/training-evaluation/SKILL.md`.
- For attention heatmaps, `create_heatmaps.py`, YAML/process-list validation, ROI heatmaps, sampled patches, or checkpoint visualization, read `sub-skills/heatmap-visualization/SKILL.md`.
- For install/import, OpenSlide, optional encoder checkpoints, GPU/runtime, or cross-workflow failures, start with `references/troubleshooting.md`.

## Pipeline Order

1. Prepare WSIs with the fast coordinate pipeline: segment tissue, generate `patches/<slide>.h5`, and optionally create masks/stitches for QC.
2. Extract patch features from those coordinate bags and original slides into feature `h5_files/` and `pt_files/`.
3. Prepare dataset CSVs and splits, then train or evaluate CLAM/MIL models against the feature root.
4. Use trained checkpoints plus heatmap YAML configuration to render attention heatmaps and sampled high-attention patches.

## Key CLAM Facts

- CLAM is script-oriented rather than an installable Python package; public workflows run repository scripts such as `create_patches_fp.py`, `extract_features_fp.py`, `main.py`, `eval.py`, and `create_heatmaps.py` from a CLAM working tree or equivalent copy.
- The documented environment targets Python 3.10 with OpenSlide, PyTorch, torchvision, timm, h5py, pandas, PyYAML, OpenCV, matplotlib, scikit-learn, scipy, tqdm, openslide-python, smooth-topk, and tensorboardX.
- `resnet50_trunc` is the default encoder; `uni_v1` needs `UNI_CKPT_PATH`; `conch_v1` needs the CONCH package plus `CONCH_CKPT_PATH`.
- ResNet50 and UNI features use `--embed_dim 1024`; CONCH features use `--embed_dim 512` in training, evaluation, and heatmap configs.
- Heavy native runs can require WSIs, OpenSlide system libraries, GPU memory, pretrained encoder checkpoints, and trained model checkpoints. Use bundled helpers for command/config preflight before launching expensive jobs.

## Public Setup Check

From a CLAM working tree, follow the upstream public setup path:

```bash
conda env create -f env.yml
conda activate clam_latest
```

For optional CONCH feature extraction, also install the upstream CONCH package and set `CONCH_CKPT_PATH`; for UNI, set `UNI_CKPT_PATH` to the downloaded checkpoint. After setup, run this minimal source-tree import check from the CLAM working tree before launching heavy workflows:

```bash
python -c "import torch, openslide, pandas; from models.model_clam import CLAM_SB; from dataset_modules.dataset_generic import Generic_MIL_Dataset; print('CLAM import ok')"
```

## References

- Read `references/pipeline-overview.md` for a concise end-to-end map of CLAM inputs, scripts, outputs, and handoffs between sub-skills.
- Read `references/troubleshooting.md` for cross-cutting install/import, OpenSlide, encoder, data-layout, GPU, and script-working-directory failures.
- Read `references/repo-provenance.md` when deciding whether this skill is stale relative to the source repository.
- `references/repo-routing-metadata.json` is structured metadata used by the managed repo-skills router during import.

## Bundled Scripts

- Run `scripts/clam_preflight.py --help` for a safe, dependency-light checklist that validates expected CLAM workflow paths and reminds agents which sub-skill owns each stage.
- Sub-skills include deeper workflow helpers for preprocessing command generation, preset CSV creation, feature extraction command generation, split/train/eval command generation, and heatmap YAML validation.

## Safety Notes

- Do not tell a future user to rely on this generated skill's source checkout or artifact reports at runtime; use bundled references and scripts.
- Do not run WSI processing, feature extraction, model training, checkpoint evaluation, or heatmap generation without confirming required data, checkpoints, runtime hardware, and output locations.
- Prefer fast dry-run helpers and YAML/CSV validation before launching GPU-heavy or storage-heavy CLAM jobs.
