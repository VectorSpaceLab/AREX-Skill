# Shared configuration map

Read this reference when a request spans lifecycle, provider, backend, GPU,
state, or export settings. Values below describe the repository's YAML surface;
the narrow sub-skill references explain behavior and recovery.

## Project and execution

```yaml
project:
  name: "my-research"
  brief: "PROJECT_BRIEF.md"
  workspace: "./workspace"
execution:
  mode: "local"                 # local | ssh | slurm
  ssh_host: ""
  remote_workspace: ""
  remote_python: "python3"
  ssh_args: []
```

`--project` is required by `python -m core.loop`. The current memory manager
reads the project-root `PROJECT_BRIEF.md` and, when a non-default
`project.workspace` is used, the application has a documented split: controller
state/directives/ledger/journals use the configured workspace while
`MEMORY_LOG.md` remains under the literal project `workspace/`. Prefer the
standard workspace unless that split is deliberately validated.

For `slurm`, also set `slurm_partition` and `slurm_time`. Optional fields are
`slurm_gpus_per_job`, raw `slurm_gres`, `slurm_qos`, `slurm_account`, trusted
operator `slurm_setup`, `slurm_extra_sbatch`, `slurm_unknown_grace_polls`, and
`slurm_time_buffer`. The scheduler assigns GPUs; the CLI `--gpu` value is
ignored for Slurm jobs.

## Provider and loop controls

```yaml
agent:
  provider: "anthropic"         # or openai, claude_cli, codex_cli, or preset
  model: "claude-sonnet-4-6"
  base_url: ""
  api_key_env: ""
  auth_token_env: ""
  max_cycles: -1
  max_steps_per_cycle: 3
  cooldown_interval: 300
  no_progress_fallback_threshold: 3
  max_cycles_per_hour: 0
monitor:
  poll_interval: 900
  zero_llm: true
  notify_on_complete: true
experiment:
  mandatory_dry_run: true
  max_parallel: 1
```

Use provider environment-variable names, never secret values. Domestic preset
labels and endpoint overrides belong to the provider sub-skill. Keep
`mandatory_dry_run: true`, use a finite `max_cycles` for a first run, and do not
interpret `max_parallel` as permission for concurrent controller workers.

## Durable progress and export

```yaml
ledger:
  enabled: true
  recent_in_context: 5
  metric_key: ""
  metric_direction: "higher_better"
stagnation:
  enabled: true
  threshold_cycles: 3
  min_delta: 0.0
journal:
  enabled: true
  max_chars: 4000
  tail_in_context: 1500
safety:
  enabled: true
  fail_threshold: 3
  stale_state_hours: 6
gates:
  enabled: false
  threshold: 0.0
  direction: "higher_better"
obsidian:
  enabled: false
  vault_path: ""
  project_subdir: "DeepResearcher/{project_name}"
  dashboard_note: "Dashboard.md"
  daily_dir: "Daily"
  auto_append_daily: true
  local_fallback_dir: "progress_tracking"
```

Memory caps default to a 3,000-character brief, 2,000-character rolling log,
1,200-character milestone section, and 15 recent decisions. `metric_key` is
required for meaningful stagnation/gate signals. A missing metric is not zero.

## Selection order

1. Validate the project brief and YAML without side effects.
2. Select the execution backend and verify required fields.
3. Select a provider and credential/CLI availability; keep worker provider
   compatible with authoritative text tool calling.
4. Probe local GPU status, or route scheduler/remote resources to the backend
   sub-skill.
5. Enable ledger/journals/safety before long runs; enable Obsidian only after
   confirming the target write location.
6. Launch a bounded experiment only after the worker's dry-run succeeds.
