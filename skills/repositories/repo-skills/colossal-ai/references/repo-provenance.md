# Repository Provenance

schema: `disco.repo-provenance.v1`

## Source Snapshot

- Skill id: `colossal-ai`
- Public project name: ColossalAI / Colossal-AI
- Python distribution: `colossalai`
- Import package: `colossalai`
- Package version observed during generation: `0.5.0`
- Source commit: `4f9953be335ef371b3848719ddafe596c01ecd37`
- Branch: `main`
- Exact tag: none observed at the source commit
- Remote URL: `https://github.com/hpcaitech/ColossalAI.git`
- Working tree state at generation: dirty due to generated `skills/` outputs.

## Evidence Paths

Runtime skill content was derived from these relative paths:

- `README.md`, `CHANGE_LOG.md`, `CONTRIBUTING.md`, `LICENSE`
- `setup.py`, `version.txt`, `requirements/requirements.txt`, `requirements/requirements-test.txt`
- `.cuda_ext.json`, `.compatibility`, `pytest.ini`, `.github/workflows/build_on_schedule.yml`
- `colossalai/`, especially `initialize.py`, `cli/`, `booster/`, `zero/`, `shardformer/`, `pipeline/`, `inference/`, `moe/`, `nn/`, `checkpoint_io/`, and `testing/`
- `docs/source/en/get_started/`, `docs/source/en/basics/`, `docs/source/en/features/`, `docs/source/en/advanced_tutorials/`, and `docs/source/en/Colossal-Auto/`
- `examples/tutorial/`, `examples/language/`, `examples/images/`, `examples/inference/`
- `applications/README.md` and application README/setup/requirements/scripts under `applications/ColossalChat`, `applications/Colossal-LLaMA`, `applications/ColossalEval`, `applications/ColossalQA`, and `applications/ColossalMoE`
- selected native tests under `tests/test_config`, `tests/test_booster`, `tests/test_zero`, `tests/test_shardformer`, `tests/test_infer`, `tests/test_pipeline`, `tests/test_tensor`, and `tests/test_moe`

## Installed Package Facts Verified During Generation

- `colossalai` imports successfully and reports version `0.5.0`.
- Distribution metadata for `colossalai` reports version `0.5.0`.
- PyTorch `2.5.1+cu124` was used for inspection and CUDA was available on NVIDIA A100 GPUs.
- CLI help checks passed for `colossalai`, `colossalai run`, and `colossalai check`.
- `colossalai check -i` completed and reported ColossalAI/PyTorch/CUDA compatibility fields; system CUDA/AOT build fields were `N/A` in the inspection environment.
- API signatures were inspected for launch helpers, `Booster`, Booster plugins, `InferenceConfig`, `InferenceEngine`, `ShardConfig`, `ShardFormer`, `GeminiDDP`, `GeminiAdamOptimizer`, and `LowLevelZeroOptimizer`.
- A one-process `torchrun` smoke initialized ColossalAI with NCCL and constructed `TorchDDPPlugin`, `LowLevelZeroPlugin`, `GeminiPlugin`, `HybridParallelPlugin`, and `Booster(TorchDDPPlugin)`.

## Refresh Guidance

Refresh this skill when package metadata, CLI launch semantics, Booster plugin signatures, ShardFormer policies, inference APIs, or first-party application dependency/command flows change.
