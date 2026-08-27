# Rendering and Evaluation CLI Reference

## render.py

Primary flags:

| Flag | Default | Notes |
|---|---:|---|
| `--model_path` / `-m` | required through combined args | Trained model root. |
| `--iteration` | `-1` | `-1` means latest saved iteration. |
| `--skip_train` | `False` | Do not render train cameras. |
| `--skip_test` | `False` | Do not render test cameras. |
| `--quiet` | `False` | Suppress timestamped log chatter. |

`render.py` also accepts the shared loading and pipeline parameters from `arguments/__init__.py`, because it calls `get_combined_args(parser)` after adding `ModelParams` and `PipelineParams`:

- `--source_path` / `-s`
- `--images` / `-i`
- `--eval`
- `--resolution` / `-r`
- `--white_background` / `-w`
- `--train_test_exp`
- `--convert_SHs_python`
- `--convert_cov3D_python`
- `--debug`
- `--antialiasing`

## get_combined_args Behavior

`get_combined_args` first parses command-line args, then tries to read `<model_path>/cfg_args`, evaluates it as an argparse `Namespace`, and merges command-line non-`None` values over the saved config.

Implications:

- A model directory produced by training normally carries the original source path, image folder, background, eval split, and pipeline options.
- For portable/pretrained models, explicitly pass `-s <source-scene>` if the saved source path is not valid in the current environment.
- If `cfg_args` is missing, render commands need enough explicit arguments to construct the scene.

## metrics.py

Primary flags:

| Flag | Required | Notes |
|---|---:|---|
| `--model_paths` / `-m` | yes | One or more model directories. |

The script expects each model directory to contain a `test/` directory with method subdirectories such as `ours_30000`, each containing `renders/` and `gt/` PNGs. It prints metrics and writes `results.json` plus `per_view.json`.

## full_eval.py

Primary flags:

| Flag | Required when | Notes |
|---|---|---|
| `--skip_training` | optional | Skip training phase. |
| `--skip_rendering` | optional | Skip rendering phase. |
| `--skip_metrics` | optional | Skip metric phase. |
| `--output_path` | optional | Defaults to `./eval`. |
| `--use_depth` | optional | Adds depth training flags. |
| `--use_expcomp` | optional | Adds exposure-compensation flags. |
| `--fast` | optional | Adds Sparse Adam optimizer flag. |
| `--aa` | optional | Adds antialiasing flag. |
| `--mipnerf360` / `-m360` | required unless both training and rendering are skipped | MipNeRF360 root. |
| `--tanksandtemples` / `-tat` | required unless both training and rendering are skipped | Tanks&Temples root. |
| `--deepblending` / `-db` | required unless both training and rendering are skipped | Deep Blending root. |

`full_eval.py` launches commands with `os.system`, so paths with spaces require extra care and full runs should be explicit user decisions.
