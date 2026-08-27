# Bounded workflows

These recipes are planning templates. Replace placeholders only after the
 dataset/environment owner confirms their contract. The commands intentionally
start with conservative side-effect settings and must not be copied unchanged
into a real hardware session.

## 1. Inspect a policy and environment

```bash
python scripts/check_policy_environment.py --policy act --device cpu
python scripts/check_policy_environment.py --policy smolvla --device cuda
```

Interpret results as gates:

- registry gate: the policy name is known;
- class gate: the lazy `modeling_*` class imports;
- dependency gate: required optional packages are available;
- device gate: requested device is available;
- execution gate: still unproven until a checkpoint, features, processors,
  and a bounded synthetic batch are checked.

Do not pass a Hub ID to this probe expecting weights to be tested; it does not
download or instantiate pretrained assets.

## 2. Fresh bounded training plan

First inspect the dataset through the dataset workflow and obtain metadata/stats.
Then construct a dry-run command similar to:

```bash
lerobot-train \
  --dataset.repo_id=ORG/DATASET \
  --policy.type=act \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --batch_size=4 \
  --steps=20 \
  --save_freq=10 \
  --save_checkpoint=true \
  --wandb.enable=false \
  --output_dir=outputs/train/policy_smoke
```

Run the smoke only after checking the output directory is new or explicitly
approved for replacement. Verify that a first batch reaches `forward`, loss is
finite, an optimizer step occurs, and a checkpoint can be loaded locally. Scale
steps/batch/workers only after the smoke is sound. Use `--eval_steps` only when
the dataset has `eval_split > 0`; set `--env_eval_freq=0` until the simulator
handoff is complete.

For a VLA or policy requiring a checkpoint, use the checkpoint path and scoped
extra; do not change its processor files merely to silence a shape error. For a
fine-tune, use `--policy.path=CHECKPOINT` and a new output directory. This is
not the same as resume: optimizer, scheduler, sampler, and RNG restoration
requires `--resume=true --config_path=...`.

## 3. Resume a run

A local resume source can be a checkpoint `train_config.json` or its
`pretrained_model` directory. A permitted Hub run source can resolve the latest
checkpoint. Use:

```bash
lerobot-train \
  --config_path=CHECKPOINT_OR_RUN_SOURCE \
  --resume=true \
  --output_dir=outputs/train/resumed_run \
  --wandb.enable=false
```

LeRobot prefers the checkpoint configuration on resume; explicit CLI overrides
still win. If the original output directory is absent, the resolver chooses a
fresh resume output directory unless `--output_dir` is supplied. Inspect
`checkpoints/<step>/pretrained_model/`, `train_config.json`, and training state
before deciding that a resume source is complete. Do not treat a plain policy
folder with only weights as a full optimizer/RNG resume.

## 4. Offline evaluation on a simulator

After the simulator owner provides a valid env configuration and its extra:

```bash
lerobot-eval \
  --policy.path=CHECKPOINT_OR_HUB_ID \
  --env.type=pusht \
  --eval.n_episodes=2 \
  --eval.batch_size=1 \
  --eval.use_async_envs=false \
  --policy.device=cuda \
  --policy.use_amp=false \
  --eval.recording=false
```

The checkpoint must include matching config/weights/processors. Use
`--rename_map` only for a documented feature-name mapping. If the environment
uses Hub code, obtain explicit consent before `--trust_remote_code=true`.
Increase episodes and vector batch size only after action shape, reset behavior,
and metrics are correct. Recording or pushing eval datasets is a separate
approved side effect.

## 5. Real-robot rollout planning

First use `lerobot-rollout --help` and the bundled safety checker. Then require
all of: calibrated and tested robot/teleoperator, camera stream matching the
checkpoint, bounded `--duration`, explicit `--task`, device gate, a safe empty
workspace test, an emergency-stop plan, and a human observer. Start with
`--strategy.type=base`, `--inference.type=sync`, no recording, and a very short
finite duration. Hardware execution is out of this sub-skill's authority unless
the user separately requests it and the robot-control-data-collection route
approves the handoff.

For large/slow chunking VLAs, `--inference.type=rtc` can run asynchronous chunk
inference. It is not a generic speed switch: confirm `policy.supports_rtc()` and
policy-specific execution horizon, queue threshold, delay, and guidance fields.
Interactive mode keeps hardware and policy warm but only supported strategies
may use it; it does not remove the need for an emergency stop.

## 6. PEFT fine-tune plan

PEFT requires a pretrained base checkpoint. Install the smallest policy extra
plus `peft` (the composite `peft` extra is available), then choose
`--peft.method_type`, `--peft.r`, optional `--peft.lora_alpha`,
`--peft.target_modules`, and `--peft.full_training_modules`. Keep a new output
folder and use a short smoke. The adapter output is not a standalone base
policy: loading it requires its PEFT config to name the base model, and
`make_policy` loads the base policy before applying the adapter.

`use_peft=true` without a checkpoint is rejected because the adapter config
cannot define the base policy. PEFT is currently rejected in sharded training.
Do not merge adapters or claim portability without checking the policy-specific
model and PEFT serialization behavior.
