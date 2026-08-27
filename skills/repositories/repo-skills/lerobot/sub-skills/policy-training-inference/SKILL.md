---
name: policy-training-inference
description: "Select, configure, train, evaluate, and safely plan inference for
  LeRobot policies, processors, devices, checkpoints, and optional PEFT
  adapters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Policy training and inference

Use this sub-skill when the task names `lerobot-train`, `lerobot-eval`,
`lerobot-rollout`, a policy type or checkpoint, policy processors, CUDA/device
selection, PEFT, or rollout inference. This sub-skill covers model-side
configuration and safe command planning. Route dataset format, episode schema,
features, and statistics acquisition to `dataset-workflows`; route physical
robot/teleoperator operation and data collection to
`robot-control-data-collection`; route simulator installation, environment
configuration, and RL to `simulation-and-rl`.

## Safety and operating boundary

- Treat training, Hub access, checkpoint downloads/uploads, W&B logging, and
  rollout as side effects. First inspect and validate; only execute after the
  user explicitly requests execution and all gates below pass.
- This skill can plan a rollout but does not authorize robot motion. Require a
  dry-run/help check, a bounded duration, a tested robot/camera/teleoperator
  handoff, an emergency stop, and a human at the controls before any hardware
  command.
- Never call a CPU import or CPU model construction proof a CUDA execution
  proof. A requested `cuda` device must be checked with `torch.cuda.is_available()`
  and the intended policy/dependencies must be importable.
- Prefer local checkpoints with `local_files_only` for offline validation. Hub
  identifiers may trigger downloads when the real command runs; ask before that.
- Do not invent a policy type. Confirm it is registered, its modeling module can
  be imported, and its scoped extra is installed.

## Inputs and outputs

Collect: LeRobot version, policy type or checkpoint, dataset/environment handoff,
feature keys/shapes, normalization statistics source, device/backend and VRAM,
training or evaluation budget, output directory, resume source, optional PEFT
settings, credentials/Hub consent, and whether real hardware is involved.

Produce one of:

1. a validated, bounded training command plan and expected checkpoint layout;
2. an evaluation plan with checkpoint, environment, episode, recording, and
   device gates; or
3. a rollout plan that remains explicitly blocked until hardware safety gates
   pass.

Record unknown feature/stat/processor provenance as an unresolved validation item,
not as a successful compatibility claim.

## Fast routing workflow

1. **Choose policy.** Start with `act` for a small/single-task baseline. Consider
   `diffusion` for action-distribution experiments; `smolvla`, `pi0`, `pi05`,
   `pi0_fast`, or other VLA policies only when the language/vision checkpoint,
   tokenizer, memory, and GPU budget are known. See
   [model-overview.md](references/model-overview.md).
2. **Check the scoped extra.** The base package supplies core policy machinery;
   optional policies use extras such as `diffusion`, `pi`, `smolvla`, `groot`,
   `wallx`, `xvla`, `peft`, or `training`. Missing dependencies must be fixed by
   the smallest relevant extra, not `all` by default.
3. **Resolve the config.** For a fresh policy, construct a registered config
   with `make_policy_config(type, ...)` and obtain input/output features from
   dataset metadata or an environment. For a checkpoint, load its
   `config.json` through `PreTrainedConfig.from_pretrained`; preserve its type
   and processor contract unless a deliberate override is validated.
4. **Build the model and processors.** `make_policy` requires exactly one of
   dataset metadata or environment config. It infers action outputs and missing
   input features, validates visual consistency, places the model on
   `config.device`, and loads safetensors for a normal checkpoint. Build the
   matching pre/post pipelines with `make_pre_post_processors`; for a checkpoint
   load the saved `policy_preprocessor.json` and `policy_postprocessor.json`.
5. **Validate one synthetic batch.** Confirm observation names, image channel/order
   and shape, state/action dimensions, task/text fields, batch dimensions, finite
   normalized values, model output shape, and postprocessed action shape before
   launching a long run. Use `step_through` or `transform_features` to locate a
   processor mismatch.
6. **Bound the run.** Use a short smoke run first (`steps` small, no Hub push,
   W&B disabled, fixed output directory). Then choose checkpoint frequency,
   evaluation split/episodes, workers, accumulation, mixed precision, and output
   policy. Do not reuse a non-empty output directory unless `resume=true`.
7. **Handoff.** Dataset and simulator owners must confirm their contracts. A
   real-robot owner must confirm robot, camera, teleop, calibration, and stop
   controls before `lerobot-rollout` is considered runnable.

## CLI decision points

- `lerobot-train` uses dotted draccus fields: `--dataset.repo_id`,
  `--policy.type`, `--policy.device`, `--batch_size`, `--steps`,
  `--output_dir`, `--save_freq`, `--eval_steps`, `--parallelism.*`,
  `--accelerator.*`, `--peft.*`, and `--resume`/`--config_path`.
- For a pretrained policy, use `--policy.path=<local-dir-or-hub-id>` in the
  current CLI contract. For a resume, use `--resume=true --config_path=<checkpoint
  train_config.json, pretrained_model directory, or permitted Hub run source>`.
  Do not confuse fine-tuning from `--policy.path` with restoring optimizer/RNG/
  sampler state via `--resume`.
- `lerobot-eval` needs `--policy.path`, `--env.type`, and bounded
  `--eval.n_episodes`; `--eval.batch_size=1` is the conservative first check.
  Recording is off unless explicitly enabled. Hub environments additionally
  require `--trust_remote_code=true` consent.
- `lerobot-rollout` is the deployment engine. `strategy.type=base` does not
  record and must not receive a dataset; sentry/highlight/dagger/episodic need
  the appropriate recording dataset, and dagger needs a teleoperator. `sync`
  works for all policies; `rtc` is for supported slow chunking policies and
  requires policy-specific queue/horizon validation.
- Run the bundled probes/builders before copying a command into a shell:
  [check_policy_environment.py](scripts/check_policy_environment.py),
  [train_command_builder.py](scripts/train_command_builder.py),
  [eval_command_builder.py](scripts/eval_command_builder.py), and
  [rollout_help.py](scripts/rollout_help.py). They print commands and checks but
  never start training, inference, downloads, simulators, or hardware.

## Training and checkpoint rules

`TrainPipelineConfig.validate()` requires a policy or reward model, disallows
an existing output directory for a fresh run, applies the policy optimizer and
scheduler presets by default, and requires a nonzero dataset `eval_split` when
`eval_steps > 0`. A normal checkpoint contains a policy config and
`model.safetensors`; processor JSON/state files must accompany it for faithful
inference. Training checkpoints also contain `train_config.json` and training
state. Safetensors is the compatible default; DCP model artifacts require a
sharded run. Sharded training currently rejects PEFT, fp16, in-training env
rollouts, reward-model training, multiple optimizers, compile/activation
checkpointing placeholders, and context parallelism greater than one.

`PreTrainedPolicy.from_pretrained` puts the policy in eval mode; call
`train()` only for training. The base contract requires `get_optim_params`,
`reset`, `forward`, `predict_action_chunk`, and `select_action`. `forward`
returns `(loss, logging_dict_or_none)`; inference calls `reset()` at episode
start and `select_action()` after preprocessing. Keep logging values native and
avoid passing gradient-bearing tensors into logs.

## Final validation checklist

- `python -m ... --help`/CLI help succeeds in the target environment.
- `check_policy_environment.py` reports the registered choice, optional package
  status, policy class import, requested device, CUDA availability, and any
  import failure without claiming execution readiness when a gate is missing.
- The exact checkpoint has `config.json`, weights, and matching pre/postprocessor
  files; revision and local-only policy are explicit.
- Dataset/environment feature names are mapped deliberately; `rename_map` is
  used only when the checkpoint contract requires it, and normalization stats
  are from the intended dataset or an explicitly approved override.
- One bounded batch passes through preprocessor → policy → postprocessor with
  finite tensors and the expected action dimension.
- Training has a new/approved output directory, bounded steps, checkpoint policy,
  no unintended Hub/W&B side effects, and a resume source if applicable.
- Evaluation has bounded episodes and recording disabled unless requested.
- Rollout has hardware/safety approval, finite duration, correct device, tested
  cameras, and emergency-stop readiness. Otherwise report `blocked`, not ready.

## Bundled reference map

- [model-overview.md](references/model-overview.md): registered policy catalog,
  scoped extras, and conditional selection guidance.
- [configuration.md](references/configuration.md): config dataclasses, dotted
  fields, feature/device construction, and distributed restrictions.
- [api-reference.md](references/api-reference.md): verified factory, policy,
  processor, serialization, normalization, and device signatures.
- [workflows.md](references/workflows.md): bounded training, resume, eval, PEFT,
  and rollout planning recipes.
- [cli-reference.md](references/cli-reference.md): safe train/eval/rollout CLI
  fields and side-effect gates.
- [troubleshooting.md](references/troubleshooting.md): dependency, checkpoint,
  device, training, evaluation, and rollout recovery.

