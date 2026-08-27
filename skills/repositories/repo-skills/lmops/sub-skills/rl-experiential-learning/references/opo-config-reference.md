# OPO configuration reference

OPO means **On-Policy RL with Optimal Reward Baseline**. In LMOps evidence, OPO is a focused VeRL configuration and algorithm modification rather than a full experiential-learning workflow like OEL, OPCD, Coach, or GAD.

Use the bundled planner for a safe configuration checklist:

```bash
python scripts/verl_experiment_planner.py --family opo --stage config --exp-name <EXP_NAME> --model <MODEL_OR_ID> --batch-size <GLOBAL_BATCH_SIZE>
```

The planner prints configuration keys only. It does not run VeRL, Ray, vLLM, or training.

## Exact on-policy training changes

For exact on-policy training, keep the policy update batch equal to the rollout batch and remove KL/entropy regularization. The required key changes are:

| Setting | Required value | Why |
| --- | --- | --- |
| `data.train_batch_size` | `<GLOBAL_BATCH_SIZE>` | Defines the full batch collected from the current policy. |
| `actor_rollout_ref.actor.ppo_mini_batch_size` | `<GLOBAL_BATCH_SIZE>` | Makes the PPO update consume the same batch instead of subdividing into stale mini-batches. |
| `actor_rollout_ref.actor.use_kl_loss` | `False` | Disables actor-side KL loss for the exact on-policy setting. |
| `actor_rollout_ref.actor.kl_loss_coef` | `0.0` | Ensures no actor KL coefficient remains active. |
| `actor_rollout_ref.actor.entropy_coeff` | `0.0` | Removes entropy regularization from the exact on-policy recipe. |
| `algorithm.kl_ctrl.kl_coef` | `0.0` | Disables algorithm-level KL control. |

A safe skeleton is:

```bash
python -m verl.trainer.main_ppo \
  algorithm.adv_estimator=grpo \
  data.train_batch_size=<GLOBAL_BATCH_SIZE> \
  actor_rollout_ref.actor.ppo_mini_batch_size=<GLOBAL_BATCH_SIZE> \
  actor_rollout_ref.actor.use_kl_loss=False \
  actor_rollout_ref.actor.kl_loss_coef=0.0 \
  actor_rollout_ref.actor.entropy_coeff=0.0 \
  algorithm.kl_ctrl.kl_coef=0.0 \
  actor_rollout_ref.model.path=<MODEL_OR_ID> \
  trainer.experiment_name=<EXP_NAME> \
  <OTHER_USER_APPROVED_KEYS>
```

Do not mix this exact on-policy recipe with OEL/OPCD/Coach/GAD command presets unless the user explicitly asks to port OPO into another VeRL workflow and accepts the algorithmic change.

## Optimal reward baseline

The optimal reward baseline is an implementation-level change to advantage computation. In an OPO checkout, the implementation label is the VeRL PPO core-algorithm module named `verl/trainer/ppo/core_algos.py`; the README evidence states that both GRPO and Reinforce++ advantage computation were extended there.

Planner-level checks:

1. Confirm the target checkout actually includes the OPO variant of the VeRL core algorithms module.
2. Confirm which advantage estimator is selected, such as GRPO or Reinforce++.
3. Confirm the optimal reward baseline code path is active for that estimator.
4. Confirm KL and entropy coefficients are zero if the user is asking for exact on-policy OPO rather than a regularized variant.
5. Confirm reward normalization/baseline logging is visible in the target run logs before treating results as OPO results.

This runtime skill cannot verify the modified advantage code by importing or executing VeRL; it only preserves the required configuration and handoff checks.

## Compatibility notes

- OPO evidence references VeRL version `v0.2.0`. Treat other VeRL versions as ports that need source review.
- OPO is not a data-preparation pipeline. Bring your own dataset, reward function, model, rollout parameters, and target trainer setup.
- Exact on-policy settings may increase memory pressure because the global train batch and PPO mini-batch are intentionally equal.
- If a user asks for OPO inside OEL, OPCD, Coach, or GAD, make the conflict explicit: those scripts have their own KL, rollout, and stage assumptions. Porting OPO means changing the algorithm recipe, not just adding one flag.

## Minimal handoff checklist

- Global batch size selected and equalized across train and PPO mini-batch settings.
- Actor KL loss disabled and KL/entropy coefficients zeroed.
- Advantage estimator selected and compatible with the optimal reward baseline implementation.
- Target VeRL checkout identified as the OPO-modified checkout.
- Ray/vLLM/GPU execution remains user-run and unverified by this skill.
