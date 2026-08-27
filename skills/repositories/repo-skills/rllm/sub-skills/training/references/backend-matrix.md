# Training Backend Matrix

| Backend | CLI/API signal | Requires | Best for | Key validation notes |
| --- | --- | --- | --- | --- |
| `tinker` | `--backend tinker`, `TinkerBackend`, `TinkerSFTBackend` | Tinker client/service credentials; optional `tinker` dependencies | Managed RL/SFT runs with Tinker sampling/training service | Sampling temperature/top_p away from 1.0 warns because logprobs can be unreliable; `training.num_minibatches != 1` is only lightly tested; router replay is not supported. |
| `verl` | `--backend verl`, `VerlBackend`, `VerlSFTBackend` | Local distributed stack, CUDA GPU, heavy `verl` dependencies | Local RL/SFT with colocated or separated distributed workers | RL path requires async rollout mode; separated/async mode requires `fwd_bwd_group_size == mini_batch_size`; `partial_rollout` cannot be combined with `remote_runtime`; `cupy` is required for NCCL checkpoint engine in separated mode. |
| `fireworks` | `--backend fireworks`, `FireworksBackend`, `FireworksSFTBackend` | Fireworks SDK, `FIREWORKS_API_KEY`, managed training infra | Fireworks managed RL/SFT | Fused forward/backward+optim unsupported; loss aggregation modes are constrained; router replay `R2` unsupported; save frequency must align with async sync interval. |

## SFT backend notes

- `rllm sft` supports backends `tinker`, `verl`, and `fireworks`.
- `--gpus` applies to the distributed Verl torchrun launcher.
- `--lora-rank 0` requests full fine-tuning; positive values configure LoRA.
- `--tokenize-method` accepts `cumulative`, `stepwise`, or `hf_template`.
- `--lr-schedule` accepts `constant`, `linear`, or `cosine`, but backend support and exact schedule behavior are backend-specific.

## Remote runtime and gateway

Training rollouts may run inside a local agent-flow engine, a remote runtime, or sandboxed tasks. The gateway gives each rollout a session-specific OpenAI-compatible base URL and records traces for enrichment. Remote sandbox/runtime paths may need public tunnels or provider-specific credentials.
