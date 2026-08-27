# TimeMixer Cross-Cutting Troubleshooting

Use this page for install/import issues, CLI boot problems, or runtime errors that do not belong to one narrower sub-skill. For dataset schemas, model tensor shapes, benchmark recipes, or task-specific workflows, route to the matching sub-skill's troubleshooting file.

## Install or import failures

| Symptom | Likely cause | Next step | Route |
| --- | --- | --- | --- |
| `ModuleNotFoundError` for `torch`, `pandas`, `sktime`, `einops`, or `PyWavelets` | The runtime environment is missing the source repository's core dependencies. | Install the repo requirements, or use the bundled environment check to see which module is missing first. | `scripts/check_timemixer_environment.py` |
| `ModuleNotFoundError` for `data_provider`, `models`, or `exp` | The checkout root is not on `sys.path`. | Run the bundled helpers from a TimeMixer checkout or pass `--repo-root` to the helper scripts. | `scripts/check_timemixer_environment.py` |
| Import succeeds but `run.py` fails later | Optional dependencies for the selected task branch are missing. | Read the CLI reference and the relevant sub-skill before choosing the command path. | `references/cli-reference.md` |

## CLI boot problems

### `run.py --help` fails with a percent-format error

The source CLI help text contains an unescaped percent sign in the anomaly-ratio help string. Argparse formats help strings with `%`, so `python run.py --help` can fail before printing the help page.

**What to do instead**

- Use `references/cli-reference.md` for the required arguments and task mapping.
- Use `sub-skills/forecasting-experiments/scripts/build_timemixer_command.py` or `sub-skills/universal-tasks/scripts/build_universal_task_command.py` to inspect generated commands safely.
- If you are debugging a private checkout, escape the percent as `%%` locally, but do not treat that edit as a benchmark result.

## Data and checkpoint path failures

| Symptom | Likely cause | Next step | Route |
| --- | --- | --- | --- |
| `FileNotFoundError` for `./dataset/...` | The benchmark dataset is not present at the expected relative path. | Read the data-preparation sub-skill and validate the dataset layout before retrying. | `sub-skills/data-preparation/SKILL.md` |
| `checkpoint.pth` not found during test-only mode | Training wrote to a custom checkpoint directory or the experiment settings changed. | Rebuild the exact training setting or copy the checkpoint to the default path expected by the test branch. | `sub-skills/forecasting-experiments/SKILL.md` |
| `test_results/` or `results/` is empty | The command was run in a mode that prints metrics but does not persist the expected artifacts. | Read the relevant workflow reference to confirm what each task branch writes. | Forecasting or universal-task sub-skills |

## Hardware and fallback issues

- The repository can be smoke-tested on CPU for model shapes and command construction.
- The host may expose CUDA GPUs, but the selected skill scope does not require CUDA benchmark reproduction.
- For a reliable CPU fallback in `run.py` commands, prefer `CUDA_VISIBLE_DEVICES=''` or the bundled command builders' `--no-use-gpu` flag rather than `--use_gpu False`.

## Shape or task-routing symptoms

| Symptom | Likely cause | Next step | Route |
| --- | --- | --- | --- |
| `RuntimeError` about channel count or shape mismatch | The wrong sub-skill constructed the command or the loader dimensions do not match the model config. | Check whether the issue is data layout, model shape, or task-specific logic and switch to the matching sub-skill. | `model-architecture`, `data-preparation`, or `universal-tasks` |
| Classification works for one feature but fails for multiple | The default channel-independent path does not fit the multivariate UEA classification branch. | Set `channel_independence=0` or use the model-architecture smoke helper for a clear diagnosis. | `sub-skills/model-architecture/` |
| Imputation or anomaly detection produces NaNs | The chosen mask or input window leaves no observed values for a batch/channel. | Confirm the data layout and mask logic, then rerun the task-specific troubleshooting page. | `sub-skills/universal-tasks/` |

## When to stop

Stop and ask for a user decision if the fix would require:

- downloading large external datasets;
- changing GPU/driver/toolkit state;
- rewriting benchmark-scale training settings;
- or mutating a checkout that should stay untouched.
