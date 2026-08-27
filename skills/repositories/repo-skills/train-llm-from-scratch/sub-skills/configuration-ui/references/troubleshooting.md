# Configuration and UI troubleshooting

Use this when config edits, command construction, Streamlit launches, UI job
state, or metrics display behave unexpectedly. Keep training/data/model diagnosis
with the owning sibling sub-skills once the issue is no longer config/UI-owned.

## Unknown config keys are ignored

**Symptom:** a JSON edit appears to have no effect, and trainer startup prints a
message like `ignoring unknown key`.

**Cause:** the loader drops keys that are not fields on the selected stage
config dataclass. This is intentional: unknown keys warn but do not fail the
run.

**Recovery:**

1. Run the trainer with `--print-config` and inspect the resolved JSON before
   launching a long job.
2. Compare the explicit JSON keys against [configuration.md](configuration.md).
3. Remove misspelled keys or keys that belong to another stage. Route loss,
   model, or data consequences to the appropriate sibling sub-skill.

## JSON `null` becomes Python `None`

**Symptom:** `--print-config` shows `null`, or the UI writes an empty optional
string as `null`.

This is expected. JSON `null` maps to Python `None` and is the correct way to
disable nullable fields such as `amp_dtype` in CPU smoke configs. Do not use the
string `"null"`; it is a normal string and will not behave like `None`.

## Smoke configs use a sibling base

**Symptom:** editing the full `configs/base.json` does not change a smoke run,
or smoke mode stays tiny/CPU after full config edits.

**Cause:** when a stage JSON lives in a directory that also contains `base.json`,
the loader uses that sibling base. For example, `configs/smoke/sft.json` uses
`configs/smoke/base.json`.

**Recovery:** edit the smoke sibling base for smoke shared fields, or use the
full stage JSON if the CUDA/full base is intended. Confirm resolution with a
safe print-only command:

```bash
python scripts/train_sft.py --config configs/smoke/sft.json --print-config
```

## Boolean CLI parsing surprises

**Symptom:** a boolean override does not act like a shell flag.

**Cause:** config booleans require a value. `1`, `true`, and `yes` parse as
true; any other provided string parses as false. A bare flag such as
`--use_wandb` is invalid because the parser expects a value.

Use explicit values:

```bash
python scripts/train_sft.py --use_wandb true --print-config
python scripts/train_sft.py --compile false --print-config
```

## CLI override precedence

**Symptom:** a JSON value seems to lose to a command-line value, or a UI save
does not affect a launch that still has an extra CLI override.

Remember the merge order: dataclass defaults < base JSON < stage JSON < CLI
field overrides. CLI `--field VALUE` applies only to that command. The UI writes
JSON files; it does not preserve ad hoc shell overrides unless those are added
to the constructed command.

## Missing Streamlit extra

**Symptom:** `streamlit run ui/app.py` fails with `command not found` or import
errors for Streamlit, pandas, or Altair.

**Recovery:** install the UI extra in the active environment:

```bash
pip install -e ".[ui]"
```

For pages that invoke training or data preparation, also install the training
extra and a suitable PyTorch build:

```bash
pip install -e ".[train,ui]"
```

Do not hard-code machine-specific interpreter or environment paths into reusable
commands.

## GPU-busy guard blocks launch

**Symptom:** the UI disables a GPU training Launch button and reports another
job is occupying the GPUs.

**Cause:** the control panel intentionally allows only one live GPU job at a
time. It scans the UI job registry for records with `kind="gpu"` and a live
PID. This avoids two full training runs competing for the same cards.

**Recovery:**

1. Let the existing job finish or stop it from its page.
2. Use smoke mode for a CPU config check.
3. If the UI appears wrong, confirm whether the recorded PID is still alive
   before changing registry files. The guard should not be blocked by dead PIDs.

## Stale UI job registry

**Symptom:** Home still lists old jobs, status is confusing after a refresh, or
a log path in a job card no longer exists.

The UI job registry is persistent so jobs survive Streamlit reruns and page
navigation. Old records may remain after a process exits. A stale record is
informational unless it points to a live GPU job. If a registry JSON is corrupt,
the UI treats that record as absent; relaunching the job recreates it.

Before cleaning old registry or log files, confirm no matching process group is
still running. Do not remove records for active `torchrun` workers.

## UI process log is missing

**Symptom:** the live log pane is empty or says no log exists.

The UI process log is separate from training metrics. It appears only after a
job has been launched by the UI. If the command was launched from a shell, the
UI may have no process log for it. For UI jobs, first check the job status and
then the job's recorded log file.

## Metrics JSONL is missing

**Symptom:** the Metrics panel says no metrics are available, or a helper cannot
find a JSONL metrics file.

Check:

1. The job has reached a logging step; many stages do not log on every step.
2. The resolved `log_dir` from `--print-config`.
3. The process is rank 0/main process; only the main process writes metrics and
   checkpoints.
4. The filename prefix expected by the stage.

Use the bundled helper to inspect any candidate metrics JSONL:

```bash
python sub-skills/configuration-ui/scripts/inspect_metrics_jsonl.py /path/to/metrics.jsonl
```

## DPO metric prefix mismatch

**Symptom:** the UI searches for `dpo_*.jsonl` but the expected DPO chart is
empty, especially after running ORPO or KTO through the DPO trainer.

The DPO-family trainer can name metrics with the concrete loss-type prefix, such
as `dpo_dpo_...jsonl`, `dpo_orpo_...jsonl`, or `dpo_kto_...jsonl`, while the UI
stage key is simply `dpo`. Search the metrics directory for the concrete
loss-type prefix and inspect the newest matching JSONL.

## Malformed or mixed metrics rows

**Symptom:** charts skip columns, or the metrics helper reports malformed or
non-object lines.

The metrics logger writes one JSON object per line. Manual edits, interrupted
writes, copied shell output, or partial appends can leave bad lines. Keep the
file for audit, but rely on the helper's malformed-line count, valid row count,
last valid row, and numeric min/max summary to decide whether enough usable
metrics remain.

## W&B optional failures

**Symptom:** training prints that W&B was disabled or unavailable.

This is not a training failure by itself. The metrics logger catches W&B
import/init exceptions and continues with local JSONL logging. Prefer
`use_wandb=false` for deterministic local debugging unless credentials, network
policy, and project settings are already configured.

## Route out when the root cause is not config/UI

- Data file shapes, HDF5 datasets, SFT masks, preference rows, and RL prompt
  schemas: [../data-preparation/SKILL.md](../../data-preparation/SKILL.md).
- CUDA memory, checkpoint shape mismatch, DDP hang, and legacy pretraining
  behavior: [../model-pretraining/SKILL.md](../../model-pretraining/SKILL.md).
- SFT/RM/DPO/PPO/GRPO objectives, reward, KL, rollout, and optimization
  behavior: [../post-training-rlhf/SKILL.md](../../post-training-rlhf/SKILL.md).
- GSM8K evaluation, answer extraction, checkpoint chat, and sampling behavior:
  [../evaluation-chat/SKILL.md](../../evaluation-chat/SKILL.md).

## Quick safe triage sequence

1. Run the relevant trainer with `--print-config`; do not start training yet.
2. Compare explicit JSON keys with `scripts/print_config_summary.py`.
3. For UI issues, inspect job status, live PID state, and process log location.
4. For metrics issues, inspect the newest candidate JSONL with
   `scripts/inspect_metrics_jsonl.py`.
5. Route data, model, training, or evaluation-specific issues to the owning
   sibling sub-skill.
