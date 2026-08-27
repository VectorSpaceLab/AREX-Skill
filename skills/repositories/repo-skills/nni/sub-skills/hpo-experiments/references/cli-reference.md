# nnictl CLI Reference

`nnictl` controls NNI experiments from the shell. Prefer help/config/log/status commands during diagnosis; only run `create`, `resume`, `stop`, `trial kill`, `experiment delete`, or cloud launches when the user confirms the target experiment and side effects.

## Help And Version

```bash
nnictl --help
nnictl --version
nnictl create --help
nnictl experiment --help
nnictl trial --help
nnictl log --help
nnictl algo --help
```

If `nnictl` fails before showing help with `ModuleNotFoundError: No module named 'pkg_resources'`, install or pin a setuptools version that still provides `pkg_resources` in the user's NNI environment. This checkout's CLI imports `pkg_resources` at startup.

## Experiment Lifecycle

| Command | Purpose | Caution |
| --- | --- | --- |
| `nnictl create --config config.yml` | Launch an experiment from YAML. | Starts manager processes, schedules trials, and may open a port. |
| `nnictl create --config config.yml --port 8088` | Launch on a specific REST/WebUI port. | Check for port collisions first. |
| `nnictl create --config config.yml --debug` | Launch with debug logging. | Debug mode is noisier and loosens some internal validation. |
| `nnictl resume EXPERIMENT_ID --port 8088` | Resume a stopped experiment. | Resume the intended ID only; external experiment dirs need explicit paths. |
| `nnictl view EXPERIMENT_ID --port 8088` | View a stopped experiment. | Useful for read-only inspection. |
| `nnictl stop` | Stop current running experiment. | Side-effecting. Confirm when multiple experiments may be running. |
| `nnictl stop EXPERIMENT_ID` | Stop a specific experiment. | Prefix matching can stop a matching experiment; avoid ambiguous prefixes. |
| `nnictl stop --port 8080` | Stop experiment on a port. | Safe only after verifying the port owner. |
| `nnictl stop --all` | Stop all experiments. | Destructive to active runs; ask first. |

## Live Inspection

```bash
nnictl experiment status
nnictl experiment show
nnictl experiment list
nnictl experiment list --all
nnictl trial ls
nnictl trial ls --head 10
nnictl trial ls --tail 10
nnictl webui url
nnictl config show
nnictl log stdout --tail 100
nnictl log stderr --tail 100
nnictl log trial --trial_id TRIAL_ID
```

Use these before changing configs. If the user reports failed trials, collect `experiment status`, `trial ls`, `log stderr`, and the exact `trialCommand` before editing the search space or tuner.

## Updating A Running Experiment

```bash
nnictl update searchspace --filename new_search_space.json
nnictl update searchspace EXPERIMENT_ID --filename new_search_space.json
nnictl update concurrency --value 4
nnictl update duration --value 2h
nnictl update trialnum --value 100
```

Cautions:

- Validate the new search-space file before updating.
- Some tuners cannot handle arbitrary runtime search-space changes even though the command exists.
- Increase concurrency only after checking local GPU/CPU capacity or remote machine capacity.

## Trial Controls

```bash
nnictl trial ls
nnictl trial kill --trial_id TRIAL_ID
```

Killing a trial changes experiment results and can affect tuner behavior. Confirm the trial ID and reason first.

## Import And Export Trial Data

Export completed trial results:

```bash
nnictl experiment export EXPERIMENT_ID --filename trials.json --type json --intermediate
```

Import prior tuning data:

```bash
nnictl experiment import EXPERIMENT_ID --filename import_data.json
```

Import file shape for built-in tuners that support it:

```json
[
  {"parameter": {"x": 0.5, "y": 0.9}, "value": 0.03},
  {"parameter": {"x": 0.4, "y": 0.8}, "value": {"default": 0.05}}
]
```

Import caveats:

- Each `parameter` object must match the experiment search space keys.
- `value` follows `nni.report_final_result()` scalar rules.
- TPE, Anneal, GridSearch, MetisTuner, and BOHB are documented as supporting import data.
- BOHB imports may need a `TRIAL_BUDGET` field in `parameter`; otherwise BOHB can use `max_budget`.

## Custom Algorithm Commands

```bash
nnictl algo register --meta_path meta_file.yml
nnictl algo list
nnictl algo show ALGORITHM_NAME
nnictl algo unregister ALGORITHM_NAME
```

Meta file shape:

```yaml
algoType: tuner
builtinName: mytuner
className: my_tuner.MyTuner
classArgsValidator: my_tuner.MyClassArgsValidator
```

Troubleshoot registration by checking:

- `algoType` is `tuner`, `assessor`, or `advisor`.
- The package/module is importable in the environment where `nnictl` runs.
- `className` includes module and class name.
- `classArgsValidator`, when present, imports and accepts the supplied config `classArgs`.

## Config And File Safety

- `trialCodeDirectory` contents are copied or sent to training services; keep it small and use `.nniignore` for remote/cloud services.
- Avoid running `platform clean`, `experiment delete`, `experiment delete --all`, or `stop --all` without explicit user confirmation.
- Do not paste real passwords, cloud tokens, access keys, or SSH passphrases into examples or generated configs.
- When debugging user configs, redact secrets before storing snippets in notes.

## Deprecated Or Internal Commands

- `nnictl ss_gen` is marked deprecated; prefer explicit search-space JSON.
- `nnictl package` is replaced by `nnictl algo`.
- `nnictl trainingservice` and `jupyter-extension` are internal/preview surfaces; route only if the user is explicitly working on those integrations.
