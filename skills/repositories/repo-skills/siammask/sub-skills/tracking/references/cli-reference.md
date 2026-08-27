# Tracking CLI Reference

## Bundled Wrapper Modes

Use `scripts/run_tracking.py` rather than invoking checkout-local scripts directly. Global flags:

- `--repo-root <path>`: SiamMask checkout to operate on.
- `--python <path>`: Python executable from the prepared environment.
- `--run`: execute; omit for dry-run command printing.
- `--strict`: fail early when resolvable checkpoint/config/result paths are missing.

## `demo` Mode

Purpose: interactive OpenCV ROI demo over an image sequence.

Important options:

- `--experiment`: usually `siammask_sharp`.
- `--resume`: checkpoint path.
- `--config`: config path, default `config_davis.json`.
- `--base-path`: image sequence directory, default `data/tennis` resolved under checkout root.
- `--cpu`: passed through, but the legacy demo still auto-selects visible CUDA when present.

Use a display-capable session. Do not use this for headless verification.

## `test` Mode

Purpose: generate benchmark tracking/segmentation outputs.

Important options:

- `--experiment`: `siammask_sharp`, `siammask_base`, or `siamrpn_resnet`.
- `--resume`: checkpoint path.
- `--config`: experiment config such as VOT/DAVIS/base config.
- `--dataset`: `VOT2016`, `VOT2018`, `VOT2019`, `DAVIS2016`, `DAVIS2017`, or `ytb_vos` when data exists.
- `--mask`: enable mask output.
- `--refine`: enable refine mask output; pair with a refine-capable checkpoint.
- `--cpu`: force CPU in the legacy test entry point.
- `--save-mask`: save segmentation masks for VOS-style output.
- `--video`: restrict to one video when supported by the dataset loader.
- `--visualization`: show OpenCV windows; avoid on headless hosts.

`test` writes checkout-local result directories and logs.

## `eval` Mode

Purpose: compute VOT accuracy, robustness, and EAO metrics from existing result folders.

Required options:

- `--dataset`: VOT dataset name.
- `--result-dir`: root containing tracker result folders.
- `--tracker-prefix`: prefix used to select tracker directories.

Optional options:

- `--num`: multiprocessing worker count.
- `--show-video-level`: include per-video details.

## `tune-vot` Mode

Purpose: sweep VOT hyperparameters.

Options mirror `test`, plus range strings:

- `--penalty-k start,end,step`
- `--window-influence start,end,step`
- `--lr start,end,step`
- `--search-region start,end,step`

This can launch many tracker runs. Keep dry-run until runtime and disk usage are approved.

## `tune-vos` Mode

Purpose: tune DAVIS/YouTube-VOS mask thresholds and tracking hyperparameters.

Important difference: the legacy VOS tuning script calls CUDA unconditionally. Treat CUDA as required with no CPU substitute for this mode.

## Native Behavior Captured by the Wrapper

- The wrapper sets the selected experiment directory as working directory because model files import experiment-local `custom.py` and config paths are relative to that directory.
- The wrapper prepends both checkout root and experiment directory to `PYTHONPATH`.
- The wrapper prints the exact command and environment prelude before execution.
- Missing checkpoints/configs are warnings by default and hard errors with `--strict`.
