# Training Workflows

## Purpose

Use this reference for the local training, evaluation, and cloud-submission
commands.

## Local training

The basic command is:

```bash
lumi train -c ./config.yml
```

Useful flags:

- `--config` / `-c`: one or more YAML config files, merged left to right.
- `--override` / `-o`: dot-notation config override such as
  `model.network.num_classes=3`.
- `--job-dir`: override the job directory from the CLI.

What to expect:

- `train.job_dir` and `train.run_name` control where checkpoints and summaries
  are written.
- The actual files are stored under `<job_dir>/<run_name>`.
- The training loop writes TensorBoard summaries and can save a run snapshot.
- If `train.job_dir` is missing, checkpoints and logs will not be saved.

### Minimal example

```bash
lumi train -c ./config.yml -o model.network.num_classes=20
```

## Evaluation

The basic command is:

```bash
lumi eval -c ./config.yml --split val
```

Useful flags:

- `--split`: dataset split to evaluate.
- `--watch / --no-watch`: keep watching for new checkpoints or stop after the
  current run of checkpoints.
- `--from-global-step`: only consider checkpoints after a given global step.
- `--files-per-class`: how many visualization files to show per class.
- `--max-detections`: cap detections used during evaluation.

### What the evaluator needs

`lumi eval` requires a config that resolves `train.job_dir` and `train.run_name`.
Without those keys it cannot find the run directory.

## Configuration flow

The training code resolves configuration in this order:

1. Default model base config.
2. Custom config files passed with `--config`.
3. Dot-notation overrides passed with `--override`.
4. Optional CLI `--job-dir` override for local training.

## Google Cloud workflow

The cloud training helpers wrap the same config and package logic but submit the
run to Google Cloud ML Engine. Use them only when you already have:

- a Google Cloud project,
- a service account key in `GOOGLE_APPLICATION_CREDENTIALS`,
- the required Compute Engine, ML Engine, and Cloud Storage APIs enabled,
- a dataset uploaded to Cloud Storage,
- and the `luminoth[gcloud]` dependency group installed.

The main commands are:

```bash
lumi cloud gc train --config ./config.yml
lumi cloud gc evaluate --train-folder gs://bucket/lumi_job --split val
lumi cloud gc jobs
lumi cloud gc logs --job-id my-job
```

### Cloud notes

- The cloud training helper packages the current Luminoth version into a source
  tarball and uploads it to the bucket.
- The cloud evaluator can reuse the training package or rebuild it.
- Cloud jobs write their results under `lumi_<job_id>` in the selected bucket.

## What to read next

- `references/configuration.md` for the config keys and model families.
- `references/cloud.md` for the GCP prerequisites and command details.
- `references/troubleshooting.md` for config, checkpoint, and cloud errors.
- `scripts/check_config_keys.py` for a safe preflight check.
