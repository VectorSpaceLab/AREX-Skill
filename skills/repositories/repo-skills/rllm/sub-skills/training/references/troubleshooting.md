# Training Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Only async rollout mode is supported for VerlBackend` | Verl RL config uses a non-async rollout mode | Set `actor_rollout_ref.rollout.mode: async` for rLLM-native Verl training. |
| `fwd_bwd_group_size == mini_batch_size` assertion | Separated/async Verl config mismatch | Align `rllm.async_training.fwd_bwd_group_size` with `mini_batch_size`. |
| `partial_rollout is not supported with remote_runtime` | Async partial rollout combined with remote runtime | Disable partial rollout or the remote runtime path. |
| `Checkpoint engine nccl not registered` or preflight `cupy` error | Missing `cupy` for separated/async Verl checkpoint sync | Install the CUDA-matching `cupy-cuda12x` or `cupy-cuda13x` wheel. |
| `only KL-in-loss is supported` | Config enables KL in reward on native Verl path | Disable `algorithm.use_kl_in_reward`; use loss-side KL. |
| Reward model unsupported on rLLM-native Verl path | `reward.reward_model.enable=True` | Compute rewards in the workflow/evaluator instead. |
| `router_replay` rejected on Tinker | Tinker backend does not support router replay | Disable router replay for Tinker. |
| Fireworks rejects fused fwd/bwd/optim | `fuse_forward_backward_and_optim_step` enabled | Set it to false for Fireworks. |
| Fireworks `save_freq` rejected | Save frequency not aligned to async sync interval | Make `save_freq` a multiple of `trigger_parameter_sync_step`. |
| SFT data validation fails | Missing/malformed `messages` rows | Inspect or recurate the dataset; see `sft-data-and-config.md`. |
| Gateway trace enrichment misses tokens/logprobs | Provider/worker did not return requested token/logprob data | Check gateway config and provider support; see root `references/gateway-and-traces.md`. |
| CLI train cannot resolve evaluator | Dataset lacks verifier/catalo reward and no `--evaluator` | Add verifier metadata or pass an evaluator explicitly. |

Do not downgrade required-backend failures to ordinary skips in verification. Preserve missing CUDA/service credentials as `BLOCKED_REQUIRED_BACKEND` unless the user narrows scope.
