# Configuration and dotted fields

LeRobot uses draccus dataclasses and `ChoiceRegistry` dispatch. Dotted CLI values
are parsed into nested config objects; a bare `--policy`/`--dataset`/`--env`
value can name a config file, while `--policy.path` is the checkpoint path
consumed by train/eval/rollout config handling.

## Policy config contract

`PreTrainedConfig` fields shared by policies include:

- `n_obs_steps` (default 1), `input_features`, `output_features`;
- `device` (`cpu`, `cuda`, `cuda:0`, `mps`, or `xpu`); `use_amp`;
- `use_peft`, `pretrained_path`, `pretrained_revision`;
- Hub metadata: `push_to_hub`, `repo_id`, `private`, `tags`, and `license`.

Construction calls `__post_init__`: an unavailable requested device is replaced
with the automatically selected device, and AMP is disabled when unavailable.
This fallback is convenient for inspection but must not be silently accepted for
a requested GPU run; inspect the warning and the effective device.

Every concrete config supplies policy-specific action/observation timing and
feature validation. Common fields include `chunk_size`, `n_action_steps`,
`horizon`, `normalization_mapping`, model/tokenizer IDs, and dtype/vision
settings. Exact defaults vary and should be obtained from the checkpoint config
or `--help`, not copied across policy families.

`make_policy_config("act", **overrides)` resolves the registered config class.
`PreTrainedConfig.get_known_choices()` is the authoritative built-in registry
in this release. `get_policy_class("act")` then lazy-imports `ACTPolicy`; this
is the preferred check before constructing a heavy model.

## Feature construction

`make_policy(cfg, ds_meta=..., env_cfg=..., rename_map=...)` requires exactly one
of `ds_meta` or `env_cfg`. Dataset metadata is preferred for training because it
provides feature definitions and normalization stats. The factory maps dataset
features to policy features, sets action outputs, fills missing inputs, stores
selected metadata/stats, and validates visual feature consistency unless a
rename map is being used. Environment-derived features are suitable for
simulation/evaluation but a fresh policy without dataset stats warns that
normalization values are not meaningful.

Feature keys and shapes are part of the checkpoint contract. Typical keys use
`observation.state`, `observation.images.<camera>`, language/task fields, and
`action`; actual names come from the dataset/environment. Use a deliberate
`rename_map` for a checkpoint whose camera/state names differ. Do not change
camera order, image resolution, action dimension, or gripper convention without
an explicit policy-specific adaptation.

## Training config

`TrainPipelineConfig` contains:

- `dataset`, optional `env`, exactly one trainable `policy` or reward model;
- `output_dir`, `job_name`, `resume`, `seed`;
- dataloader controls: `num_workers`, `batch_size`, `prefetch_factor`,
  `persistent_workers`, and multiprocessing context (default `spawn`);
- `steps`, `log_freq`, `save_freq`, `save_checkpoint`, `checkpoint_format`;
- `eval_steps`, `max_eval_samples`, `env_eval_freq`;
- optimizer/scheduler presets, `parallelism`, `accelerator`, `ema`, `wandb`,
  `peft`, `job`, and optional sample weighting/rename map.

Fresh runs reject an existing `output_dir`; `resume=true` is required to reuse
one. Policy presets populate optimizer/scheduler unless
`use_policy_training_preset=false`, in which case both must be provided. An
`eval_steps > 0` request needs `dataset.eval_split > 0`. A policy configured to
push to Hub needs `policy.repo_id` for local runs. Keep `wandb.enable=false`,
`push_to_hub=false`, and `save_checkpoint_to_hub=false` during a smoke plan.

## Evaluation and rollout config

`EvalPipelineConfig` has `env`, `eval`, optional `policy`, `output_dir`,
`job_name`, `seed`, `rename_map`, and `trust_remote_code`. `EvalConfig` defaults
to 50 episodes, auto-selects a batch size when zero (capped at 64 and episode
count), uses async vector environments by default, and does not record. Set a
small explicit episode count and `batch_size=1` for the first check.

`RolloutConfig` combines optional robot/teleoperator, `policy`, polymorphic
`strategy` (`base`, `sentry`, `highlight`, `episodic`, `dagger`), polymorphic
`inference` (`sync`, `rtc`), optional recording dataset, `fps`, bounded
`duration`, `interactive`, `device`, `task`, visualization, `rename_map`, and
compile settings. Base strategy rejects a dataset; recording strategies need a
repository; DAgger needs a teleoperator. `interactive=true` is only supported
by strategies that declare interactive support.

## Distributed/accelerator fields

- `--parallelism.dp_replicate`, `--parallelism.dp_shard`, context-parallel
  ring/ulysses degrees, and `cfg_parallel` describe topology. Context parallel
  and CFG parallel values greater than one are currently rejected for training.
- `--accelerator.mixed_precision` is `no`, `fp16`, or `bf16`.
- `--accelerator.gradient_accumulation.steps` must be at least one.
- FSDP wrap modules and size threshold are mutually exclusive. Compile and
  activation-checkpointing are configured placeholders and fail validation when
  enabled in this release.
- Sharded training supports `no`/`bf16`, not `fp16`, and rejects PEFT,
  in-training environment evaluation, reward-model training, and multi-optimizer
  configs. DCP checkpoint formats require a sharded run.
