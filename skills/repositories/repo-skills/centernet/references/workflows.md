# Workflows

## Purpose

Read this when you are ready to run CenterNet end to end: choose a config, train a model, resume from a checkpoint, or evaluate a saved checkpoint on COCO.

## Training flow

1. Pick a config basename from `config/`.
   - `CenterNet-52` uses `config/CenterNet-52.json`.
   - `CenterNet-104` uses `config/CenterNet-104.json`.
2. Confirm the COCO data layout in `references/data-layout.md`.
3. Build the compiled extensions and run `scripts/check_install.py --repo-root <checkout>`.
4. Launch training:
   - `python train.py CenterNet-52`
   - `python train.py CenterNet-104`
5. Resume from an iteration when a checkpoint already exists:
   - `python train.py CenterNet-52 --iter 120000`
   - `python train.py CenterNet-104 --iter 240000`
6. Use `--threads` to set the number of dataset prefetch workers. The config's `batch_size` and `chunk_sizes` should be chosen so the GPU split is sensible for the available device count.

### What training writes

- Checkpoints go under `cache/nnet/<snapshot_name>/<snapshot_name>_<iter>.pkl`.
- Training may also create cache files such as `cache/coco_<split>.pkl`.
- The model snapshot name is the `cfg_file` argument passed to `train.py`.

## Evaluation flow

1. Pick the same config basename used for training.
2. Point `--testiter` at an existing checkpoint iteration.
3. Choose a split:
   - `training` maps to `trainval`
   - `validation` maps to `minival`
   - `testing` maps to `testdev`
4. Run one of these commands:
   - `python test.py CenterNet-52 --testiter 480000 --split validation`
   - `python test.py CenterNet-104 --testiter 480000 --split testing`
5. Add `--suffix multi_scale` when you want the multi-scale config variant.
   - The command will read `config/<cfg>-multi_scale.json`.
   - Examples: `python test.py CenterNet-52 --testiter 480000 --split validation --suffix multi_scale`

### What evaluation writes

- Results go under `results/<snapshot_name>/<testiter>/<split>/`.
- A suffix adds one more directory level, such as `results/.../multi_scale/`.
- The main output is `results.json` in COCO result format.
- `--debug` adds a `debug/` directory with visualizations.

## Notes that matter in practice

- `test.py` loads the selected checkpoint before decoding detections, so a missing checkpoint is a setup problem rather than a model bug.
- `testdev` has no ground-truth COCO evaluation in this repo; the code returns after writing detections.
- `train.py` and `test.py` import the COCO API and custom ops at module import time, so build failures show up before the help text or runtime path begins.
- The repo's only registered dataset is `MSCOCO`.
