# Repo provenance

- Schema: `disco.repo-provenance.v1`

This file records the source baseline used to construct the generated AReaL repo skill.

## Source snapshot

- Repository: AReaL
- Package distribution: `areal`
- Package version from metadata: `2.0.0`
- Python support from metadata: `>=3.11,<3.13`
- Current branch: `main`
- Current commit: `1bd2cb3180492d00f7081f210eeb35a35c2617b9`
- Exact tag: none detected at the source commit
- Public remote: `https://github.com/areal-project/AReaL.git`
- Working tree state during construction: dirty because generated skill artifacts were added under `skills/`

## Evidence paths used

- Package metadata and install variants: `pyproject.toml`, `pyproject.vllm.toml`, `uv.lock`, `uv.vllm.lock`
- Source roots: `areal/api/`, `areal/dataset/`, `areal/reward/`, `areal/workflow/`, `areal/trainer/`, `areal/engine/`, `areal/infra/`, `areal/v2/`, `areal/experimental/`
- Public docs distilled into bundled references: `README.md`, `docs/en/tutorial/`, `docs/en/reference/`, `docs/en/customization/`, `docs/en/algorithms/`, `docs/en/best_practices/`, `docs/en/cli_reference.md`
- Example workflows used as evidence only: `examples/math/`, `examples/alignment/`, `examples/vlm/`, `examples/agent_workflow/`, `examples/hermes/`, `examples/swe/`, `examples/tau2/`, `examples/tir/`, `examples/scaffolding/`, `examples/skypilot/`
- Native tests used as behavior evidence and later verification candidates: `tests/test_*`, `tests/grpo/`, `tests/sft/`, `tests/v2/`, `tests/megatron/`, `tests/experimental/archon/`, `tests/torchrun/`
- Repo-maintained scripts/tools considered for bundling or reference: `scripts/uv_sync.sh`, `scripts/uv_lock.sh`, `areal/tools/*`
- Agent/maintainer guidance evidence: `AGENTS.md`, `CLAUDE.md`, repo-local agent skill directories

## Construction environment summary

A private Python 3.12 CUDA-capable inspection environment verified the package version, key module imports, CLI help, signatures for configuration/workflow/data classes, and a minimal CUDA tensor smoke. It was intentionally not an exact full AReaL release runtime: broad optional/runtime dependencies and exact backend lockfile pins were not fully synchronized. Use this generated skill as operating guidance, and verify real SGLang/vLLM/Megatron/FSDP/Archon/Ray/Slurm workflows in the user's target runtime before claiming runtime success.

## Refresh guidance

Refresh this skill when any of these change:

- `pyproject.toml` / `pyproject.vllm.toml` dependency variants or supported Python range.
- `areal/api/cli_args.py` config dataclasses, default values, or migration rules.
- `areal/api/alloc_mode.py` backend-string syntax or role allocation behavior.
- Trainer, dataset, reward, workflow, engine, v2 service, or CLI public contracts.
- Example workflow command patterns, service lifecycle recipes, or troubleshooting advice.
- AReaL release version, public runtime image tags, or backend package pins.
