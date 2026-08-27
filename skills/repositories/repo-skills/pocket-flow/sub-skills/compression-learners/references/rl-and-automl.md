# RL Hyperparameter Search and AutoML Bridge

PocketFlow uses reinforcement learning as a learner-internal hyperparameter optimizer for selected compression learners. This is separate from the source repository's AutoML/Seven wrapper, which is an external job bridge for hparam files and result parsing. Use [execution-config AutoML notes](../../execution-config/references/automl.md) for the wrapper mechanics; use this reference for the compression meanings of learner flags.

## Which learners expose RL search?

| Learner | RL trigger | What the agent chooses | Reward / evaluation signal | Notes |
| --- | --- | --- | --- | --- |
| `channel` | `--cp_prune_option auto` | Layer-wise preserve/compression actions for channel pruning. | `--cp_reward_policy accuracy` or `flops`, with `--cp_noise_tolerance` guarding extreme speedup/noise. | Uses `--cp_nb_rlouts` and `--cp_nb_rlouts_min`. This is the original channel-pruning learner, not `chn-pruned-rmt`. |
| `weight-sparse` | `--ws_prune_ratio_prtl optimal` | Layer-wise weight pruning ratios. | `--ws_reward_type single-obj` or `multi-obj`; fast evaluation uses `--ws_nb_iters_feval`. | Uses `--ws_nb_rlouts` and `--ws_nb_rlouts_min`. Requires pretrained full model for the optimal protocol. |
| `uniform` | `--uql_enbl_rl_agent=True` | Layer-wise weight bit-widths under a total bit budget. | Accuracy after optional global/layer-wise fine-tuning. | Uses `uql_*` RL flags and DDPG common flags. Activations usually stay at the fixed `--uql_activation_bits` setting. |
| `non-uniform` | `--nuql_enbl_rl_agent=True` | Layer-wise weight bit-widths under a total bit budget. | Accuracy after non-uniform quantization and optional tuning. | Uses `nuql_*` counterparts of the uniform learner's RL flags. |

Learners that should not be described as RL-search learners: `full-prec`, `chn-pruned-rmt` (docs say RL is not ready), `chn-pruned-gpu` (GPU pruning implementation but not the documented DDPG ratio search), `dis-chn-pruned`, and `uniform-tf`.

## DDPG operating model

The DDPG optimizer runs multiple roll-outs. In each roll-out, it traverses layers, computes a state vector, chooses an action, applies a candidate compression setting, fine-tunes/evaluates cheaply, computes reward, records transitions, and trains actor/critic networks for later roll-outs.

For quantization learners, the documented state includes:

- layer index embedding,
- weight tensor shape,
- number of parameters,
- bit budget already used,
- remaining bit budget.

For pruning/sparsification learners, the same pattern is adapted to per-layer preserve or sparsity ratios. A final high-quality model may still need a full-data retraining/fine-tuning pass after search discovers a good policy.

## Common DDPG flags

These flags are shared through the DDPG implementation. Most tasks should leave them at defaults unless the user explicitly asks to tune the optimizer itself.

| Flag | Meaning |
| --- | --- |
| `--ddpg_tau` | Target-network update coefficient. |
| `--ddpg_gamma` | Reward discount factor. |
| `--ddpg_lrn_rate` | Actor and critic learning rate. |
| `--ddpg_loss_w_dcy` | Weight decay coefficient. |
| `--ddpg_record_step` | Transition recording stride. |
| `--ddpg_batch_size` | Replay-buffer mini-batch size. |
| `--ddpg_enbl_bsln_func` | Enable the baseline function for rewards. |
| `--ddpg_bsln_decy_rate` | Baseline exponential-decay rate. |
| `--ddpg_actor_depth`, `--ddpg_actor_width` | Actor MLP architecture. |
| `--ddpg_critic_depth`, `--ddpg_critic_width` | Critic MLP architecture. |
| `--ddpg_noise_type`, `--ddpg_noise_prtl`, `--ddpg_noise_std_init`, `--ddpg_noise_std_finl` | Exploration-noise family and schedule. |

Changing these can destabilize search; prefer adjusting learner-level rollout counts and bounds first.

## Learner-level RL flags

### Original channel pruning

```text
--learner channel
--cp_prune_option auto
--cp_preserve_ratio <target-FLOPs-preserve-ratio>
--cp_nb_rlouts <total-rollouts>
--cp_nb_rlouts_min <warmup-rollouts-before-agent-training>
--cp_reward_policy accuracy|flops
```

`--cp_preserve_ratio` is a model-level computation-preservation target. It is not the same as `--cp_uniform_preserve_ratio`, which applies a uniform per-layer preserve ratio.

### Weight sparsification

```text
--learner weight-sparse
--ws_prune_ratio_prtl optimal
--ws_prune_ratio <target-sparsity>
--ws_nb_rlouts <total-rollouts>
--ws_nb_rlouts_min <warmup-rollouts>
--ws_reward_type single-obj|multi-obj
```

Schedule flags still matter after the policy is chosen:

```text
--ws_iter_ratio_beg <fraction>
--ws_iter_ratio_end <fraction>
--ws_prune_ratio_exp <exponent>
--ws_mask_update_step <interval>
```

If an AutoML bridge or old note emits `--ws_update_mask_step`, normalize it to the learner-defined `--ws_mask_update_step` before launching.

### Uniform quantization

```text
--learner uniform
--uql_enbl_rl_agent=True
--uql_equivalent_bits <average-bit-budget>
--uql_nb_rlouts <total-rollouts>
--uql_w_bit_min <min-weight-bits>
--uql_w_bit_max <max-weight-bits>
--uql_enbl_rl_global_tune=True|False
--uql_enbl_rl_layerwise_tune=True|False
--uql_tune_global_steps <steps>
--uql_tune_layerwise_steps <steps>
--uql_enbl_random_layers=True|False
```

The equivalent-bit budget limits the sum of layer-wise bits times parameter counts. If the chosen layer bits exceed this budget, the implementation raises an error rather than silently accepting an over-budget policy.

### Non-uniform quantization

Use the same pattern with `nuql_` prefixes:

```text
--learner non-uniform
--nuql_enbl_rl_agent=True
--nuql_equivalent_bits <average-bit-budget>
--nuql_nb_rlouts <total-rollouts>
--nuql_w_bit_min <min-weight-bits>
--nuql_w_bit_max <max-weight-bits>
--nuql_enbl_rl_global_tune=True|False
--nuql_enbl_rl_layerwise_tune=True|False
--nuql_tune_global_steps <steps>
--nuql_tune_layerwise_steps <steps>
--nuql_enbl_random_layers=True|False
```

Non-uniform search still optimizes compression/accuracy trade-offs, not direct integer-kernel acceleration.

## AutoML relationship

PocketFlow's source AutoML materials are not the same as learner-internal DDPG:

- Learner-internal DDPG is invoked by the flags above and runs inside the learner process.
- The source AutoML bridge is a job wrapper that consumes an hparam file, converts selected weight-sparsification schedule parameters into CLI flags, runs an external job, and parses TensorFlow logs into result fields.
- The generated skill tree owns safer AutoML converters under `execution-config`; do not treat those helpers as original PocketFlow source scripts.

AutoML hparam bridge parameters are centered on weight sparsification schedule tuning: `ws_prune_ratio_exp`, `ws_iter_ratio_beg`, `ws_iter_ratio_end`, and a mask-update-step parameter that should map to `ws_mask_update_step` for real learner runs.

## Safety and verification boundary

RL search can multiply training cost by hundreds of roll-outs. It also requires data, checkpoints, TensorFlow 1.x, and often GPU capacity. The source `rl_agents/unit_tests/*` toy scripts were treated as reference-only for this sub-skill; they are not bundled helpers and are not proof that a full learner search will converge on a user's model.
