# Streamlit control-panel UI

The control panel wraps the data pipeline, stage configs, background training
jobs, live logs, metrics charts, GSM8K evaluation, and chat in Streamlit.

## Install and launch

Install the UI extra in the environment where the repo is installed:

```bash
pip install -e ".[ui]"
streamlit run ui/app.py
```

For a full training environment, install the training extra as well:

```bash
pip install -e ".[train,ui]"
```

If `streamlit` is missing, the command will fail before the app starts. The UI
extra supplies Streamlit plus pandas/altair for charts. The training extra
supplies dataset and optional W&B integrations; it is still the training scripts,
not the UI package itself, that need GPUs and heavy data.

## Pages and ownership

| Page | What it does | Route deeper details to |
|---|---|---|
| Home | Pipeline diagram, GPU status from `nvidia-smi`, active job cards, per-stage status badges. | This sub-skill for job registry behavior; backend setup to root skill. |
| Data | Launches data-prep scripts as CPU background jobs and lists files under `/ephemeral/data`. | [../data-preparation/SKILL.md](../../data-preparation/SKILL.md) for schemas and validators. |
| Pretrain | Theory, config form, launch/stop, log tail, metrics chart for base pretraining. | [../model-pretraining/SKILL.md](../../model-pretraining/SKILL.md). |
| SFT, Reward, DPO, PPO, GRPO | Theory, config form, launch/stop, log tail, metrics chart for alignment stages. | [../post-training-rlhf/SKILL.md](../../post-training-rlhf/SKILL.md). |
| Evaluate | In-process GSM8K evaluation for checkpoints. | [../evaluation-chat/SKILL.md](../../evaluation-chat/SKILL.md). |
| Chat | In-process checkpoint chat/raw generation with sampling controls. | [../evaluation-chat/SKILL.md](../../evaluation-chat/SKILL.md). |

The stage pages all use the same renderer: theory + diagram, run tab, smoke
toggle, GPU-count slider, config form, launch/stop buttons, live log, and metric
chart.

## Config form behavior

The UI loads the resolved stage config, displays shared model/runtime fields and
stage hyperparameters separately, and writes edited values back to JSON:

- shared base/runtime fields are written to the `base.json` in the same directory
  as the selected stage JSON;
- stage-specific fields are written to the selected stage JSON;
- in smoke mode this means `configs/smoke/base.json` and
  `configs/smoke/<stage>.json`, not the full `configs/base.json`.

Empty optional-string form values are written as JSON `null`, which the loader
maps back to Python `None`. The UI also displays the resolved command it would
launch.

## Job construction and registry

The job manager builds commands as follows:

- Multi-GPU stage and `nproc > 1`: `torchrun --standalone --nproc_per_node=N SCRIPT --config JSON ...`.
- Single-process or smoke mode: `python SCRIPT --config JSON ...` using the
  environment's current Python executable.
- Data-prep jobs use normal Python commands, not `torchrun`.

When a job launches, the manager:

1. creates the persistent UI job registry directory if needed;
2. writes stdout/stderr to that registry's `<job_id>.log` file;
3. writes a registry JSON for the job with `job_id`, `pid`, `cmd`, `log`,
   `kind`, `started`, and status metadata;
4. starts the subprocess in a new process group so Stop can terminate `torchrun`
   and worker ranks together;
5. sets `PYTHONPATH` to the repo root, `HF_HOME` to the default local Hugging
   Face cache location, and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
   unless already set.

Job IDs for training pages are stable stage keys such as `pretrain`, `sft`,
`reward`, `dpo`, `ppo`, and `grpo`. Data-page IDs are slugged labels prefixed by
`data_`.

## Status, stop, and stale registry handling

Status is computed from the registry and process liveness:

- missing registry: `none`;
- live process: `running`;
- dead process with `traceback`, `error:`, or `aborted` in the log tail:
  `failed`;
- dead process without those markers: `finished`.

The liveness check treats zombie processes as dead and best-effort reaps them.
Stop sends `SIGTERM` to the job process group and records `status="stopped"` in
that job's registry. A stale registry for a dead process can still appear in the
Home job list, but it should not block the GPU guard unless the process is alive.
If a registry JSON is corrupt, the reader returns `None`; recreate it by
relaunching the job after confirming no orphan process is running.

## GPU-busy guard

The UI intentionally allows only one running GPU job at a time. It scans the
persistent UI job registry for records with `kind="gpu"` and a live PID. If it
finds one, GPU launches for other training stages are disabled and the page asks
users to stop that job or use smoke mode. CPU/smoke launches and in-process chat
remain available.

This guard prevents two multi-GPU `torchrun` runs from fighting for the same
cards and OOMing. It is a UI guard, not a cluster scheduler: if a user launches
jobs outside the UI, the registry may not know about them. Check GPU processes
separately before starting a long full run.

## Logs and metrics

Job logs are process logs under the UI job registry and are tailed in the stage
page. Training metrics are separate JSONL files under the resolved `log_dir`,
named `<stage>_<timestamp>.jsonl`.

Each JSONL metrics row is written by the main process as:

```json
{"step": 20, "wall": 1730000000.0, "train_loss": 2.3, "lr": 0.00001}
```

Different stages log different metrics. Examples include `train_loss`, `lr`,
`tok_per_s`, `eval_train`, `eval_dev`, `dev_loss`, `train_acc`, `test_acc`,
`test_margin`, `reward`, `kl_ref`, `policy_loss`, `value_loss`, `clipfrac`,
`resp_len`, `informative_groups`, and `gsm8k_acc`.

The UI finds the newest metrics file matching the stage prefix and plots numeric
columns except bookkeeping columns `step` and `wall`. For DPO, the trainer writes
metrics with a prefix based on `loss_type` such as `dpo_dpo` or `dpo_orpo`, while
the UI stage metadata uses `dpo`. If the chart says no `dpo_*.jsonl` exists,
check the configured metrics log directory for the concrete loss-type prefix.

Use the bundled metrics helper outside the UI:

```bash
python sub-skills/configuration-ui/scripts/inspect_metrics_jsonl.py /path/to/sft_1234567890.jsonl
python sub-skills/configuration-ui/scripts/inspect_metrics_jsonl.py --demo
```

It is read-only and does not require pandas, Streamlit, or repo imports.

## W&B behavior

Weights & Biases is optional. If `use_wandb` is true, the metrics logger tries to
import and initialize W&B. Any exception disables W&B and prints a message, but
local JSONL logging continues. Prefer JSONL for deterministic local debugging;
turn on W&B only when credentials and network policy are already configured.
