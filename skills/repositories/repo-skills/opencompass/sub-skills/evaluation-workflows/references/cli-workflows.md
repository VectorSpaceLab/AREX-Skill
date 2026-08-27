# OpenCompass CLI Workflows

OpenCompass exposes an installed console entrypoint named `opencompass`. Use it for runtime instructions instead of relying on source-tree scripts. The CLI accepts an optional config positional argument plus shortcut selectors such as `--models`, `--datasets`, and `--summarizer`.

## Core Execution Flow

OpenCompass evaluation has four practical phases:

1. Configure: load a `.py` config file or build one from CLI model/dataset shortcuts.
2. Inference: partition model-dataset work and write predictions under the run directory.
3. Evaluation: score predictions and write per-model results.
4. Visualization: summarize results into tables through the configured summarizer.

A normal full run uses `--mode all` implicitly:

```bash
opencompass path/to/eval_config.py -w outputs/my_experiment
```

For CLI shortcut selection:

```bash
opencompass --models hf_opt_125m hf_opt_350m --datasets siqa_gen winograd_ppl -w outputs/shortcut_eval
```

For a quick HuggingFace model definition from CLI flags:

```bash
opencompass --datasets siqa_gen winograd_ppl \
  --hf-type base \
  --hf-path facebook/opt-125m \
  --hf-num-gpus 1 \
  -w outputs/hf_eval
```

`--hf-num-gpus` is a scheduling/minimum-resource declaration for the HuggingFace model. It is not a guarantee that exactly that many GPUs are used at runtime.

## First-Run Debug Pattern

OpenCompass normally runs tasks in parallel and may redirect worker logs under the work directory. For a first run, use `--debug` so the scheduler runs tasks sequentially and prints more output in real time:

```bash
opencompass path/to/eval_config.py --debug -w outputs/debug_eval
```

Use this to validate config loading, dataset resolution, model construction arguments, and evaluator wiring before a long parallel run.

## Dry Run Pattern

Use `--dry-run` to build and print/dispatch planned task commands without actually invoking the runners. In the CLI implementation, `--dry-run` also enables debug behavior and returns before task execution.

```bash
opencompass path/to/eval_config.py --dry-run -w outputs/plan_eval
```

For a cluster planning check with two datasets and one HuggingFace model:

```bash
opencompass --datasets siqa_gen winograd_ppl \
  --hf-type base \
  --hf-path facebook/opt-125m \
  --hf-num-gpus 1 \
  --slurm -p gpu_short \
  --dry-run \
  -w outputs/slurm_plan
```

This command is suitable for command-construction review; it should not require actual model downloads, credentials, or GPU execution because `--dry-run` stops before runner execution.

## Mode Selection

Use `--mode` to limit the run stage:

- `--mode all`: run inference, evaluation, and visualization; this is the default.
- `--mode infer`: produce predictions only.
- `--mode eval`: score existing predictions; requires `--reuse` or station read flags.
- `--mode viz`: summarize existing results; requires `--reuse` or station read flags.

Examples:

```bash
opencompass path/to/eval_config.py --mode infer -w outputs/my_experiment
opencompass path/to/eval_config.py --mode eval --reuse -w outputs/my_experiment
opencompass path/to/eval_config.py --mode viz --reuse -w outputs/my_experiment
```

When `--mode eval` or `--mode viz` is used without `--reuse`, OpenCompass raises an error unless results are read from a station via `--read-from-station` and `--station-path`.

## Work Directories and Reuse

`--work-dir` (`-w`) names the base workspace. OpenCompass creates a timestamped experiment directory inside it, stores a dumped config in `configs/`, and writes logs, predictions, results, and summaries under that timestamp.

Use `--reuse` to skip already-completed artifacts and run missing jobs from a prior timestamp:

```bash
opencompass path/to/eval_config.py --mode eval --reuse -w outputs/my_experiment
```

To pin a specific timestamp:

```bash
opencompass path/to/eval_config.py --mode viz --reuse 20260621_120000 -w outputs/my_experiment
```

Checklist for failed-run recovery:

- Use the same config or an intentionally compatible config.
- Point `-w` at the same base work directory, not directly at the timestamp directory.
- Use `--reuse` with no value for latest, or with the timestamp name for deterministic recovery.
- Choose `--mode eval` when predictions exist but metrics/tables are missing.
- Choose `--mode viz` when results exist but the summary table is missing or stale.

## Runner Shortcut Flags

Local execution is the default when no config-defined runner is present and neither `--slurm` nor `--dlc` is selected:

```bash
opencompass path/to/eval_config.py --max-num-workers 2 -w outputs/local_eval
```

Slurm execution requires a partition:

```bash
opencompass path/to/eval_config.py --slurm -p gpu_partition --retry 2 -w outputs/slurm_eval
```

DLC execution requires a configured Aliyun/DLC config path:

```bash
opencompass path/to/eval_config.py --dlc --aliyun-cfg path/to/aliyun.cfg -w outputs/dlc_eval
```

If a config already defines `infer` or `eval` runners and the CLI also supplies `--slurm` or `--dlc`, OpenCompass warns that runtime arguments override the config runner for that stage.

## Safe Smoke Validation

Use the bundled script when an agent needs to prove the installed CLI exists and that representative commands can be constructed without running models:

```bash
python scripts/opencompass_cli_smoke.py --check-help
python scripts/opencompass_cli_smoke.py --show-command path/to/eval_config.py --mode eval --reuse latest -w outputs/my_experiment
```

The script does not invoke model inference. It runs `opencompass --help` only when `--check-help` is provided and otherwise prints a shell-quoted command for review.
