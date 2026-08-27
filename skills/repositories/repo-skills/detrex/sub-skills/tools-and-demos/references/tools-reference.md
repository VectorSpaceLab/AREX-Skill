# Tools Reference

This sub-skill distills the detrex command-line workflows covered by the demo, analysis, visualization, and benchmark tools. The bundled helper prints commands only; it does not execute a benchmark, download checkpoints, or scan a dataset tree.

## Command-builder contract

- Run the helper from a detrex checkout root or an installed environment that exposes the `demo` and `tools` modules.
- The helper accepts explicit config, checkpoint, input, output, and override arguments.
- For demo-style commands, it emits `--opts` followed by overrides.
- For analysis, visualization, and benchmark commands, it emits trailing `KEY=VALUE` overrides to match the source scripts.
- Use `--format json` when another agent needs a machine-readable plan.
- The helper never starts training or benchmark execution by itself.

## Workflow matrix

| Workflow | Source entry point | What it does | Inputs the user must supply | Safe command-builder note |
| --- | --- | --- | --- | --- |
| Image / video demo | `python -m demo.demo` | runs instance visualization on images, videos, or a webcam | config file, input source, and usually a checkpoint override | quote a single glob pattern safely; use `--webcam` only when you want an interactive stream |
| Model analysis | `python -m tools.analyze_model` | prints FLOPs, activations, parameters, or structure | config file, tasks, and `--num-inputs` for FLOPs / activations | keep the launcher to one GPU; only FLOPs / activations need a checkpoint |
| Data visualization | `python -m tools.visualize_data` | renders raw annotations or dataloader samples | config file, source, and output directory | `--output-dir` is the actual parser flag; do not copy the docs typo `--output_dir` |
| Prediction visualization | `python -m tools.visualize_json_results` | overlays saved predictions with dataset images | JSON input, output directory, and dataset name | the output is a directory of paired visualizations, not a single file |
| Benchmark planning | `python -m tools.benchmark` | measures train, eval, data, or data_advanced throughput | config file, task, and launch args | the helper prints a plan only; `eval` is single-GPU |

## Demo command surface

`demo.demo` accepts these key flags:

- `--config-file`
- one of `--input`, `--video-input`, or `--webcam`
- `--output`
- `--min_size_test`
- `--max_size_test`
- `--img_format`
- `--metadata_dataset`
- `--confidence-threshold`
- `--opts` for config overrides such as `train.init_checkpoint=...`

### Demo rules

- `--input` may be one image, multiple image paths, or a single glob pattern.
- `--video-input` is for a single video file.
- `--webcam` is interactive and does not support `--output`.
- When multiple images are provided, use an existing directory-style output target.
- The script loads `cfg.train.init_checkpoint`, so a missing or incompatible checkpoint will fail at load time.

### Video output behavior

The source demo chooses an OpenCV video codec and falls back when `x264` is unavailable. It may write `.mkv` or `.mp4` depending on the backend, so inspect the saved filename extension after the run.

## Analysis command surface

`tools.analyze_model` accepts:

- `--tasks flop activation parameter structure`
- `--num-inputs`
- `--config-file`
- trailing config overrides such as `train.init_checkpoint=...`

### Analysis rules

- `parameter` and `structure` are read-only and do not need a checkpoint.
- `flop` and `activation` use the test dataloader and usually need a checkpoint.
- The source script asserts `--num-gpus 1` and does not support eval-only mode.
- Use `--num-inputs` to bound the number of samples used for data-dependent statistics.

## Visualization command surface

### `tools.visualize_data`

- `--source annotation` renders raw dataset annotations.
- `--source dataloader` renders preprocessed training samples.
- `--config-file` points at the config that defines the dataset.
- `--output-dir` is the parser flag used by the script.
- `--show` opens a window instead of writing files.
- trailing overrides are allowed.

### `tools.visualize_json_results`

- `--input` points to a prediction JSON file.
- `--output` is a directory that will receive saved visualizations.
- `--dataset` selects the registered dataset metadata.
- `--conf-threshold` filters the visualized detections.

### Visualization rules

- `visualize_data` with `annotation` is finite; `dataloader` may be effectively infinite.
- `visualize_json_results` requires a dataset name that has matching category-id metadata.
- COCO and LVIS are the intended built-in paths; other datasets need compatible registration.

## Benchmark command surface

`tools.benchmark` accepts:

- `--task train eval data data_advanced`
- `--config-file`
- `--num-gpus`
- `--num-machines`
- `--machine-rank`
- `--dist-url`
- trailing config overrides

### Benchmark rules

- The helper never starts the benchmark; it only prints the command.
- `eval` is single-GPU and single-node only.
- `data` and `data_advanced` may require `psutil` at import time.
- `train` and `eval` benchmark paths can be long and resource-heavy, so keep them as explicit user choices.

## MOT and tracking routes

The generic helper does **not** wrap the project-specific MOT demo path. `demo/mot_demo.py` and the CO-MOT demo notes are reference-only because tracking state is sequence-dependent and project configs may route through a project launcher rather than the generic demo entry point.

Use a tracking route only when you have:

- a contiguous frame sequence from one video or one scene
- a tracking-capable checkpoint
- a project-specific config that is known to support that route

If you only need object detection on still images, use the generic demo workflow instead.
