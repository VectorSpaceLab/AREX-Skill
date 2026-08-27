# AgileRL Cross-Cutting Troubleshooting

## Install Or Import Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `PackageNotFoundError: No package metadata was found for agilerl` | Importing from source without installing the distribution metadata | Install with `pip install agilerl` or `pip install -e .` in a development checkout. |
| Resolver tries to download very large Torch/JAX/vLLM/DeepSpeed wheels | Core/LLM dependencies are heavy and backend-specific | Use Python 3.10/3.11, install only needed extras, and avoid `[all]` unless necessary. |
| Torch import works but CUDA is unavailable | CPU wheel, missing driver passthrough, or incompatible CUDA runtime | Use CPU for config checks; only require CUDA when training needs it, then install a wheel compatible with the driver and GPU. |
| Box2D or pygame environments fail | Optional environment dependencies or rendering libraries are missing | Install `agilerl[box2d]`, ensure `swig` is available for Box2D, or switch to non-rendering Gymnasium envs for smoke checks. |
| W&B prompts for login or raises credential errors | Training helper has logging enabled | Set the relevant `wb`/`WANDB` flag false for local smoke tests or configure W&B explicitly. |
| PettingZoo/SuperSuit import missing | Multi-agent environment extras are not installed | Install the needed PettingZoo environment package and `SuperSuit`; validate with the multi-agent helper before training. |
| LLM imports fail for `transformers`, `peft`, `vllm`, `deepspeed`, `bitsandbytes`, or `liger_kernel` | `[llm]` optional extras are missing or unsupported on the host | Install `agilerl[llm]` in a suitable Python/Linux/GPU environment, or use the LLM dependency inspection script for a dry-run plan. |

## Config And API Misuse

- `INIT_HP` keys must match the algorithm family; do not reuse DQN replay settings for PPO or LLM trainers without checking the nearest sub-skill.
- `net_config` usually contains `encoder_config` and `head_config`; multi-agent workflows may use per-agent or group-level nested config.
- `HyperparameterConfig` fields must use actual algorithm attribute names such as `lr`, `batch_size`, or `learn_step`.
- Replay samples and transitions should be tensor-compatible and include expected fields (`obs`, `action`, `reward`, `next_obs`, `done`) with the vectorized dimension when needed.
- Avoid top-level multiprocessing vector-env construction in scripts; wrap training entry points in `if __name__ == "__main__":`.

## Validation Before Expensive Runs

1. Run `../scripts/check_agilerl_install.py --check-optional`.
2. Run the nearest sub-skill `scripts/inspect_*` helper with `--help`, then a tiny smoke mode.
3. Validate observation/action spaces, `net_config`, `INIT_HP`, and optional dependency availability.
4. Only then run full training, distributed jobs, remote dataset pulls, model downloads, or benchmarks.
