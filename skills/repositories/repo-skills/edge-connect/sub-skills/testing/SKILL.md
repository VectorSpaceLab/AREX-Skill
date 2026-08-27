---
name: testing
description: "Run EdgeConnect checkpoint-backed testing and inference with
  prepared commands and checkpoint checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Testing

Use this sub-skill when the task is to run, prepare, or troubleshoot EdgeConnect test-time inference from existing checkpoints.
It covers the `test.py` wrapper, stage-specific checkpoint requirements, paired image/mask/edge inputs, output files, and safe command construction.

## Covers

- `test.py` as the thin `main(mode=2)` wrapper.
- `main.load_config(mode=2)` behavior: reads `config.yml` from `--path`/`--checkpoints`, forces `MODE=2`, defaults `MODEL=3`, forces `INPUT_SIZE=0`, and lets CLI inputs override the test flists and output path.
- CLI arguments: `--path`/`--checkpoints`, `--model`, `--input`, `--mask`, `--edge`, and `--output`.
- Stage behavior for `MODEL=1`, `MODEL=2`, `MODEL=3`, and `MODEL=4` at inference time.
- Result naming, default and explicit output locations, and `DEBUG` edge/masked side outputs.
- Checkpoint/config layout and no-network pretrained-checkpoint limitations.

## Read first

- `references/testing-workflows.md` for single-file, directory, and external-edge recipes.
- `references/checkpoint-layout.md` before choosing a stage or checkpoint directory.
- `references/troubleshooting.md` when a command runs but produces missing, random-looking, or mismatched outputs.

## Bundled helpers

- `scripts/check_checkpoints.py` validates a checkpoint directory without downloading anything or importing Torch.
- `scripts/build_test_command.py` prints a shell-quoted `python test.py ...` command from user-supplied paths and stage options; it never executes the command.

## Quick routing rules

1. Check the checkpoint directory for `config.yml` and the stage's required generator weights.
2. Decide the inference stage: edge-only, inpaint-only, edge-then-inpaint, or joint-trained edge-then-inpaint.
3. Decide whether the config uses Canny edges (`EDGE=1`) or external edges (`EDGE=2`).
4. Provide paired image and mask inputs as single files, aligned directories, or aligned flists.
5. Use an explicit output directory unless writing under the checkpoint directory is intended.
6. Route flist construction and config-path validation to `data-preparation`; route training to `training`; route PSNR/SSIM/FID scoring to `evaluation`.

## Key cautions

- Testing loads generator checkpoints only. Missing generators do not reliably stop the program; they can leave randomly initialized models, so validate first.
- `MODEL=3` and `MODEL=4` have the same test-time flow: generate edges with the edge model, then inpaint with the inpainting model.
- External edge files are used only when the checkpoint config has `EDGE: 2`.
- The bundled skill does not include pretrained weights and should not rely on network downloads during inference preparation.
- EdgeConnect is a legacy codebase; use a dependency set compatible with older SciPy/scikit-image/OpenCV/Numpy/Torch APIs when running the repository.
