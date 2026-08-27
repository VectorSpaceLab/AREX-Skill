---
schema: disco.repo-provenance.v1
skill: vllm
---

# Repository Provenance

- Skill id: `vllm`
- Source project: vLLM
- Package distribution: `vllm`
- Package version observed during inspection: `0.1.dev1+g183a430c1.cpu`
- Source commit: `183a430c137db3d5cd0b9025b816f26ee87328e7`
- Source branch: `main`
- Exact source tag: none detected
- Remote URL: `https://github.com/vllm-project/vllm.git`
- Working tree state at generation: dirty because this generated `skills/` tree and review artifacts were untracked

## Evidence Paths

- `pyproject.toml`, `setup.py`, `MANIFEST.in`, `requirements/`, `README.md`
- `vllm/` package source, especially `entrypoints/`, `config/`, `sampling_params.py`, `outputs.py`, `tool_parsers/`, `reasoning/`, `multimodal/`, `lora/`, `distributed/`, `platforms/`, and `profiler/`
- `docs/getting_started/`, `docs/cli/`, `docs/configuration/`, `docs/features/`, `docs/serving/`, `docs/deployment/`, `docs/usage/`, `docs/benchmarking/`
- `examples/basic/`, `examples/generate/`, `examples/features/`, `examples/tool_calling/`, `examples/reasoning/`, `examples/pooling/`, `examples/disaggregated/`, `examples/observability/`
- `tests/entrypoints/`, `tests/engine/`, `tests/config/`, `tests/multimodal/`, `tests/lora/`, `tests/reasoning/`, `tests/parser/`, `tests/distributed/`, `tests/benchmarks/`

## Inspection Snapshot

A private package-inspection environment verified `import vllm`, distribution metadata, `pip check`, key `LLM` and `SamplingParams` signatures, `EngineArgs.from_cli_args`, `vllm --help`, and `vllm serve --help`. The inspection backend was CPU/precompiled; GPU execution was intentionally left to user-hardware verification.

## Refresh Signals

Refresh this skill when any of these change materially:

- CLI subcommands or `vllm serve --help=all` flag groups
- `LLM`, `SamplingParams`, pooling output classes, or OpenAI request/response schemas
- Structured-output, tool-parser, or reasoning-parser backend behavior
- Multimodal media allowlist semantics, LoRA loading/resolver behavior, or pooling endpoint names
- Deployment configuration groups, parallelism modes, KV cache/offload behavior, metrics, profiling, or supported backend matrix
