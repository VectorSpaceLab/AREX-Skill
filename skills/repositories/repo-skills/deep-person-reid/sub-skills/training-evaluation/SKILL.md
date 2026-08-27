---
name: training-evaluation
description: "Train, evaluate, configure, and inspect Torchreid data workflows
  for person re-identification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Torchreid training and evaluation

Use this sub-skill when a task asks for Torchreid image/video ReID training, checkpoint evaluation, dataset/data-manager setup, YACS-style config edits, sampler/optimizer/lr-scheduler choices, mean/std analysis, or split-log parsing. It covers Torchreid 1.4.0 (`torchreid` distribution/import) and the unified `scripts/main.py`-style workflow in a self-contained form.

## Route here for

- Training or evaluating OSNet/ResNet-family ReID models on Market1501, DukeMTMC-reID, MSMT17, CUHK03, MARS, iLIDS-VID, PRID2011, or custom datasets.
- Same-domain, cross-domain, multi-source, target-training-loader, and video-ReID data manager construction.
- `ImageDataManager`, `VideoDataManager`, `Engine.run`, `ImageSoftmaxEngine`, `ImageTripletEngine`, `VideoSoftmaxEngine`, `VideoTripletEngine` usage.
- YACS config overrides such as `model.load_weights`, `test.evaluate`, `data.save_dir`, `sampler.train_sampler`, `train.lr_scheduler`, `cuhk03.classic_split`.
- Dataset layout checks, custom dataset registration, `compute_mean_std`, and `parse_test_res`-style log analysis.

## Route elsewhere

- Embedding-only APIs, `FeatureExtractor`, model-key catalogs, raw distance matrices, CMC/mAP API internals, re-ranking details, model complexity, activation maps, or ranked visualization internals: use `../feature-extraction/SKILL.md`.
- ONNX, OpenVINO, TFLite, or other deployment/export work: use `../model-export/SKILL.md`.
- Deep Mutual Learning, OSNet-AIN NAS, or PA-100K attribute-recognition project workflows are excluded long-tail gaps in this generated skill; do not claim runnable coverage unless a future extension bundles those project sources.

## Operating sequence

1. Determine whether the request is **train**, **evaluate/test-only**, **data inspection**, **config generation**, **mean/std**, or **log parsing**.
2. Check dataset type and layout in [references/data-formats.md](references/data-formats.md). Do not assume downloads are available; many public dataset links are fragile or gated.
3. Build or edit the config using [references/configuration.md](references/configuration.md). Prefer explicit dotted opts for final commands.
4. Choose the workflow recipe from [references/workflows.md](references/workflows.md). Use CUDA only as an optional performance backend unless the user has already verified it.
5. Confirm API signatures and output structures in [references/api-reference.md](references/api-reference.md) before writing code.
6. If errors appear, diagnose with [references/troubleshooting.md](references/troubleshooting.md).

## Bundled safe helpers

These scripts are safe by default: `--help` never imports heavy packages, and no helper runs training by default.

- [scripts/torchreid_train_eval.py](scripts/torchreid_train_eval.py): prints unified Torchreid train/eval command plans, merges embedded official templates or a supplied YAML config, validates common opts, and can write a resolved config.
- [scripts/compute_mean_std.py](scripts/compute_mean_std.py): checks dataset prerequisites and computes channel statistics only when `--compute` is explicitly supplied.
- [scripts/parse_test_results.py](scripts/parse_test_results.py): parses split directories containing `test.log*` files and reports missing or incomplete logs clearly.

## Safe verification quick checks

From this sub-skill directory, future agents can run:

```bash
python scripts/torchreid_train_eval.py --help
python scripts/torchreid_train_eval.py --template im_osnet_x1_0_softmax_256x128_amsgrad_cosine --mode eval --root /path/to/reid-data --weights /path/to/model.pth.tar --visrank --save-dir log/eval_osnet --dry-run
python scripts/compute_mean_std.py --help
python scripts/compute_mean_std.py /path/to/reid-data market1501 --check-only
python scripts/parse_test_results.py --help
```

Only run actual training/evaluation/mean-std computation after the user provides local datasets, checkpoint paths when needed, and compute/backend approval.
