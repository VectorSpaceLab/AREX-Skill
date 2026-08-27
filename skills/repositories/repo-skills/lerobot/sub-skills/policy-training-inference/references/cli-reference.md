# CLI reference

These are the verified LeRobot 0.6.2 entry points. Use the target environment's
`--help` as the final authority because installed plugins can add choices.

## `lerobot-train`

Core fields:

```text
--dataset.repo_id=...
--dataset.root=...
--dataset.eval_split=0.1
--policy.type=act
--policy.path=...
--policy.device=cuda|cpu|mps|xpu
--policy.use_amp=true|false
--policy.push_to_hub=false
--policy.repo_id=ORG/POLICY
--output_dir=...
--job_name=...
--resume=true|false
--config_path=...
--steps=N
--batch_size=N
--num_workers=N
--prefetch_factor=N
--persistent_workers=true|false
--dataloader_multiprocessing_context=spawn|fork|null
--save_checkpoint=true|false
--save_freq=N
--checkpoint_format=safetensors|dcp|safetensors_dcp
--eval_steps=N
--max_eval_samples=N
--env_eval_freq=N
--wandb.enable=true|false
--parallelism.dp_replicate=N
--parallelism.dp_shard=N
--accelerator.mixed_precision=no|fp16|bf16
--accelerator.gradient_accumulation.steps=N
--peft.method_type=LORA
--peft.r=N
--peft.lora_alpha=N
--peft.target_modules=...
--peft.full_training_modules=...
```

`--policy.type` is a registered choice and is distinct from `--policy.path`.
Dotted policy fields can override values read from a policy config. Avoid
passing obsolete names such as `--policy.pretrained_path` when the entry point
expects `--policy.path`; verify with help and checkpoint-loading behavior.

A distributed smoke may be launched with `torchrun` only after a single-process
smoke. The source launch contract is `torchrun --nproc-per-node=N` followed by
the installed `lerobot-train` executable. Use `dp_shard` only after policy wrap
units, dtype, checkpoint format, and restrictions are understood.

## `lerobot-eval`

```text
--policy.path=LOCAL_DIR_OR_HUB_ID
--policy.type=...
--env.type=...
--eval.n_episodes=N
--eval.batch_size=N
--eval.use_async_envs=true|false
--eval.recording=true|false
--eval.recording_repo_id=...
--eval.recording_private=true|false
--policy.device=...
--policy.use_amp=...
--rename_map={...}
--trust_remote_code=true|false
--output_dir=...
--seed=N
```

The evaluation entry point loads the policy config from `--policy.path`. A
checkpoint folder needs at least `config.json` and `model.safetensors`; faithful
inference additionally needs matching processor JSON/state. Set recording off
for the first check. `recording_repo_id` requires recording=true and should be
considered a Hub side effect.

## `lerobot-rollout`

Deployment fields include:

```text
--strategy.type=base|sentry|highlight|episodic|dagger
--inference.type=sync|rtc
--policy.path=LOCAL_DIR_OR_HUB_ID
--robot.type=...
--teleop.type=...
--task="..."
--duration=SECONDS
--fps=30
--device=cuda|cpu|mps|xpu
--interactive=true|false
--dataset.repo_id=...
--dataset.single_task="..."
--display_data=false
--resume=false
--rename_map={...}
--use_torch_compile=false
```

Base strategy is the no-recording path and rejects a dataset. Sentry, highlight,
Dagger, and episodic are recording strategies and need a recording dataset;
Dagger also needs teleoperation. Use `--duration=0` only after an explicitly
approved long-running safety plan; finite duration is the default safety gate.
`--interactive=true` leaves the robot idle until `/start` for supported
strategies but still connects hardware during setup.

## Safe parsing rules

Quote JSON/list/dict values for the shell. Use `--help` before relying on a
nested field. Never paste a command containing credential values into logs.
Hub downloads/uploads require credentials and network consent; simulator and
robot flags can have immediate side effects even when the policy itself loaded
successfully. The bundled command builders emit shell-quoted commands and
validation notes but never execute them.
