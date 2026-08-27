# Repository provenance

- Schema: `disco.repo-provenance.v1`
- Project: Nano-vLLM (`nano-vllm`)
- Source commit: `bb823b3e06983d71485a8e1f23715ebd87d98ef8`
- Branch: `main`
- Exact tag: none at the source commit
- Source tree state: clean at the recorded snapshot
- Package version: `0.2.0`
- Public homepage: `https://github.com/GeeeekExplorer/nano-vllm`
- Extraction baseline: source snapshot above; refresh this skill when public APIs, model support, CUDA dependencies, or execution behavior change.

## Evidence paths

The skill was distilled from these repository-relative sources:

- `pyproject.toml` — package metadata, Python range, dependencies, and homepage.
- `README.md` — install, model-directory, quick-start, and benchmark guidance.
- `example.py` — local Qwen3 generation workflow.
- `bench.py` — throughput benchmark workflow.
- `nanovllm/__init__.py`, `nanovllm/llm.py`, `nanovllm/sampling_params.py`, `nanovllm/config.py` — public API and configuration defaults.
- `nanovllm/engine/` — scheduling, sequence lifecycle, KV-cache blocks, multiprocessing, CUDA graphs, and model execution.
- `nanovllm/layers/` — attention, Triton KV-cache storage, tensor-parallel layers, normalization, rotary embedding, and sampling.
- `nanovllm/models/qwen3.py` — Qwen3-only model graph and packed weight mapping.
- `nanovllm/utils/` — execution context and safetensors loading.

Logo files, VCS metadata, production logs, review artifacts, and generated
outputs are not runtime evidence.
