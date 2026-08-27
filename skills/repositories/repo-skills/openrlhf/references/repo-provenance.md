# Repo Provenance

schema: `disco.repo-provenance.v1`

## Source Snapshot

- Repository: OpenRLHF
- Public remote: `https://github.com/OpenRLHF/OpenRLHF.git`
- Branch: `main`
- Commit: `3f8ae08c99db23a3532abc3159144f6a0821a6d0`
- Exact tag: none detected
- Package version: `0.10.4`
- Working tree state at generation: dirty because the generated `skills/` tree was added during DisCo generation

## Evidence Paths

- `README.md`
- `README_zh.md`
- `README_ja.md`
- `docs/ppo_examples.md`
- `docs/openrlhf_architecture.svg`
- `setup.py`
- `pyproject.toml`
- `requirements.txt`
- `version.txt`
- `openrlhf/`
- `openrlhf/cli/`
- `openrlhf/datasets/`
- `openrlhf/models/`
- `openrlhf/trainer/`
- `openrlhf/trainer/ray/`
- `openrlhf/trainer/ppo_utils/`
- `openrlhf/utils/`
- `examples/python/`
- `examples/scripts/`
- `tests/test_loss_aggregation.py`
- `tests/test_ray_env_vars.py`
- `dockerfile/`

## Generation Notes

- The generated skill covers user-facing OpenRLHF workflows: data preparation, SFT/RM/DPO training, PPO-family RL and agent training, runtime operations, and utilities.
- Private inspection verified the `openrlhf` distribution metadata and top-level import at version `0.10.4`.
- Full dependency installation and GPU runtime execution were not treated as proven because the heavyweight stack includes CUDA/DeepSpeed/Ray/vLLM/flash-attn components that require environment-specific setup.
- Expensive examples, Docker/system scripts, Ray/vLLM training, service launchers, and checkpoint conversion commands are represented as documented workflows or helpers, not as default smoke tests.

## Refresh Triggers

Refresh this skill when any of these change:

- `openrlhf/cli/*.py` argument names, defaults, or command entry behavior.
- Dataset preprocessing in `openrlhf/datasets/` or VLM processing in `openrlhf/utils/vlm_utils.py`.
- Agent executor contracts in `openrlhf/utils/agent.py` or Ray/vLLM rollout behavior in `openrlhf/trainer/ray/`.
- README examples, `examples/scripts/`, or `examples/python/` workflows.
- Dependency pins in `requirements.txt`, extras in `setup.py`, or package version in `version.txt`.
