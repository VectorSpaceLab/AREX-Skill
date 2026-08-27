# Runners and Partitioners

OpenCompass separates task splitting from task launching:

- A partitioner turns the configured model/dataset combinations into inference or evaluation task objects.
- A runner executes those task objects locally or submits them to a scheduling backend.
- The CLI fills default `infer` and `eval` runner/partitioner configs when the config omits them or when `--slurm` / `--dlc` force a launch backend.

## Default Mental Model

A config typically defines `models`, `datasets`, and optionally `infer` / `eval` sections. If `infer` or `eval` is absent, the CLI builds a default stage configuration from command-line arguments.

The stages write task outputs to stage-specific directories inside the timestamped work directory:

- Inference partitioner output directory: `predictions/`
- Evaluation partitioner output directory: `results/`
- Summarizer/visualization reads evaluation results and prints/writes tables from the same run directory.

## Partitioner Choices

### `NaivePartitioner`

Use for simple, predictable task splitting. It dispatches model/dataset combinations as independent tasks and is suitable as a baseline for inference or evaluation.

Config sketch:

```python
from opencompass.partitioners import NaivePartitioner

infer = dict(partitioner=dict(type=NaivePartitioner))
```

### `SizePartitioner`

Use for inference when datasets vary greatly in size. It estimates task cost from dataset size and task type, then splits/merges units to balance work. It is documented as unsuitable for `OpenICLEvalTask` evaluation tasks.

Config sketch:

```python
from opencompass.partitioners import SizePartitioner

infer = dict(
    partitioner=dict(type=SizePartitioner, max_task_size=5000, gen_task_coef=20),
)
```

### Worker-count partitioners

The package also contains worker-count and subjective variants such as `NumWorkerPartitioner`, `SubNaivePartitioner`, `SubSizePartitioner`, and `SubNumWorkerPartitioner`. Use them only when the config/test evidence for a workflow calls for those subjective or fixed-worker splitting semantics.

## Runner Choices

### `LocalRunner`

Use for local CPU/GPU execution and small debug runs. `--max-num-workers` caps parallel tasks, while actual concurrency is also constrained by available GPUs and per-task model requirements.

CLI example:

```bash
opencompass path/to/eval_config.py --max-num-workers 2 -w outputs/local_eval
```

Config sketch:

```python
from opencompass.runners import LocalRunner
from opencompass.tasks import OpenICLInferTask

infer = dict(
    runner=dict(type=LocalRunner, max_num_workers=2, task=dict(type=OpenICLInferTask)),
)
```

### `SlurmRunner`

Use for cluster submission. The CLI requires `--partition` (`-p`) when `--slurm` is set. `--retry` controls retry count unless overridden by the config.

CLI example:

```bash
opencompass path/to/eval_config.py --slurm -p gpu_partition --retry 2 -w outputs/slurm_eval
```

Config sketch:

```python
from opencompass.runners import SlurmRunner
from opencompass.tasks import OpenICLInferTask

infer = dict(
    runner=dict(type=SlurmRunner, max_num_workers=16, retry=2, task=dict(type=OpenICLInferTask)),
)
```

If a config already contains `infer.runner` or `eval.runner`, adding `--slurm` at launch time causes the CLI to warn that the runtime backend choice overrides that stage's config.

### `DLCRunner`

Use only when Alibaba DLC CLI/configuration is already available. The CLI checks that `--aliyun-cfg` points to an existing config file when `--dlc` is set.

CLI example:

```bash
opencompass path/to/eval_config.py --dlc --aliyun-cfg path/to/aliyun.cfg -w outputs/dlc_eval
```

Config-based DLC workflows include `aliyun_cfg` with values such as shell initialization, OpenCompass environment name, DLC config path, workspace id, and worker image. Do not fabricate those values; ask the user or inspect their deployment config.

## Task Types

OpenCompass task classes represent stage execution:

- `OpenICLInferTask`: performs OpenICL inference and writes predictions.
- `OpenICLEvalTask`: evaluates predictions and writes metrics/details.
- `OpenICLEvalWatchTask`: can support watch/daemon-style evaluation that tracks inference progress in workflows that configure it.

Task internals belong in `../../prompt-and-inference/SKILL.md`; this sub-skill only needs task types to explain runner/partitioner orchestration.

## Native Candidate Planning

Safe native-backed verification candidates for this sub-skill should avoid model execution:

- Run the bundled smoke script with `--check-help` and assert help mentions `--mode`, `--dry-run`, `--debug`, `--reuse`, `--work-dir`, `--slurm`, and `--dlc`.
- Use the smoke script `--show-command` mode to construct cluster dry-run and reuse commands, then assert the generated shell command includes the expected flags and does not execute OpenCompass.
- Inspect partitioner unit tests as evidence for task-splitting behavior; do not run full evaluation tests as sub-skill drafting validation.

## Decision Checklist

- Use `--debug` before long parallel jobs.
- Use `--dry-run` to inspect planned task commands without runner execution.
- Use `--mode infer` to produce predictions only.
- Use `--mode eval --reuse` to score existing predictions after a failed/partial run.
- Use `--mode viz --reuse` to regenerate summaries when metrics already exist.
- Use `--slurm -p PARTITION` only when the user has a Slurm partition.
- Use `--dlc --aliyun-cfg FILE` only when the user has a valid DLC configuration.
