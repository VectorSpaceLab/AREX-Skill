---
name: inference-serving
summary: Work on FastVideo public inference APIs, config-first CLI/server
  entrypoints, OpenAI/streaming contracts, and attention backends.
description: "Use when a FastVideo task touches generation, VideoGenerator, API
  schemas/parsers, CLI config translation, serving endpoints, streaming
  router/server behavior, or attention backend selection."
license: Apache 2.0
metadata:
  disco-role: operating
disable-model-invocation: true
---

# FastVideo Inference and Serving

## Activate this subskill for

- `VideoGenerator`, `PipelineConfig`, `SamplingParam`, `GeneratorConfig`, or
  `GenerationRequest` work.
- `fastvideo generate`, `fastvideo serve`, `fastvideo router-serve`, `bench`, or
  `eval` behavior.
- OpenAI-compatible image/video generation APIs.
- Streaming router/server protocols, health/readiness, GPU pool, prompt
  providers, stream encoders, or WebSocket/session behavior.
- Attention backend selection, env overrides, or backend-specific inference
  gates.

## Read first

Always read the nearest `AGENTS.md` for edited paths. Commonly relevant:

- `fastvideo/AGENTS.md`
- `fastvideo/pipelines/AGENTS.md`
- `fastvideo/attention/AGENTS.md`
- `fastvideo/tests/AGENTS.md`
- `fastvideo/tests/ssim/AGENTS.md` for quality-regression tests

User-facing docs to consult before changing behavior:

- `README.md`
- `docs/inference/inference_quick_start.md`
- `docs/inference/cli.md`
- `docs/inference/configuration.md`
- `docs/inference/optimizations.md`
- `docs/inference/support_matrix.md`
- `docs/design/server_contracts/index.md`
- `docs/design/server_contracts/openai.md`
- `docs/design/server_contracts/streaming.md`
- `docs/attention/index.md`
- `docs/attention/developer/index.md`
- `docs/contributing/attention_backend.md`
- `docs/contributing/testing.md`

## Core code map

- Public facade: `fastvideo/__init__.py`.
- Programmatic generator: `fastvideo/entrypoints/video_generator.py`.
- API schemas/parsers/presets: `fastvideo/api/` and `fastvideo/fastvideo_args.py`.
- CLI entrypoints: `fastvideo/entrypoints/cli/`.
- OpenAI-compatible server: `fastvideo/entrypoints/openai/`.
- Streaming server/router: `fastvideo/entrypoints/streaming/`.
- Pipeline config and execution: `fastvideo/configs/pipelines/` and
  `fastvideo/pipelines/`.
- Attention selector/backends/platforms: `fastvideo/attention/` and
  `fastvideo/platforms/`.

## Operating workflow

1. Classify the surface:
   - public Python API;
   - config parser/translation;
   - CLI command;
   - OpenAI server contract;
   - streaming router/server contract;
   - attention/backend capability.
2. Preserve config-first behavior. `generate`, `serve`, and `router-serve` use
   `--config` plus dotted overrides; do not add an ad-hoc CLI argument unless it
   belongs in the schema/config surface and tests cover the translation.
3. For public generation parameters, update the schema/config source before
   examples or presets use the option. Unknown sampling keys may be ignored or
   only logged depending on the path; verify with parser/schema tests.
4. For `VideoGenerator`, verify construction/signature behavior without forcing
   a model download unless the task explicitly needs generation. The inspected
   public signatures are:
   - `VideoGenerator.from_pretrained(model_path=None, **kwargs)`
   - `VideoGenerator.generate(request, *, log_queue=None)`
   - `PipelineConfig.from_pretrained(model_path)`
   - `SamplingParam.from_pretrained(model_path)`
5. For server work, keep protocol tests close to the changed contract and avoid
   starting a long-lived production server as a smoke test. Prefer safe imports,
   TestClient tests, and CLI `--help`.
6. For streaming router work, verify both data shape and lifecycle behavior:
   config parsing, health/readiness, prompt providers, session store, stream
   encoding, worker/GPU pool interactions, and WebSocket protocol compatibility.
7. For attention work, use the selector and platform APIs instead of reading
   environment variables directly from arbitrary call sites. Set
   `FASTVIDEO_ATTENTION_BACKEND` before constructing components and recreate the
   generator/model after changing it.

## Attention backend guardrails

- The process-wide env override is `FASTVIDEO_ATTENTION_BACKEND`.
- Common documented values include `TORCH_SDPA`, `FLASH_ATTN`,
  `VIDEO_SPARSE_ATTN`, `SAGE_ATTN`, `SAGE_ATTN_THREE`, `ATTN_QAT_INFER`,
  `VMOBA_ATTN`, `SLA_ATTN`, `SAGE_SLA_ATTN`, and `SLIDING_TILE_ATTN`.
- Component/requested backends can intentionally outrank the env override.
  Preserve role-specific behavior instead of forcing a global override.
- Do not mutate the env var mid-process and reuse an already constructed
  generator as proof of multiple backend selections.
- Backend availability is hardware/package-specific. If a backend requires a
  kernel package or GPU architecture that is absent, fail narrowly or choose a
  documented fallback; do not silently claim coverage from `TORCH_SDPA`.

## Suggested verification commands

Use the smallest matching subset:

```bash
python -m pip check
python skills/disco/fastvideo/scripts/verify_fastvideo_runtime.py --cuda
fastvideo --help
fastvideo generate --help
fastvideo serve --help
fastvideo router-serve --help
pytest fastvideo/tests/api/test_cli_translation.py -q
pytest fastvideo/tests/attention/test_selector_role_override.py -q
pytest fastvideo/tests/entrypoints/test_video_generator.py -q
pytest fastvideo/tests/entrypoints/test_openai_api.py -q
pytest fastvideo/tests/entrypoints/streaming/test_server.py -q
pytest fastvideo/tests/entrypoints/streaming/test_prompt_providers.py -q
```

Escalate only when needed:

```bash
pytest fastvideo/tests/ssim/ -vs
pytest fastvideo/tests/inference/ -q
fastvideo generate --config <config.yaml>
fastvideo serve --config <serve.yaml>
fastvideo router-serve --config <router.yaml>
```

Before escalation, confirm model assets, GPU memory, expected runtime, output
locations, and whether external downloads/credentials are allowed.

## Common failure diagnoses

- `fastvideo generate` or `serve` complains about missing arguments: the command
  expects `--config`; create a YAML/JSON config and use dotted overrides.
- A new API field appears in examples but not CLI/config tests: add or update
  schema/parser tests before relying on it.
- `torch.cuda.is_available()` is false in a GPU task: verify the installed torch
  CUDA wheel, driver/runtime compatibility, and container GPU visibility before
  debugging FastVideo code.
- Attention backend tests pass in one process but fail after env changes: rebuild
  the generator/model after changing `FASTVIDEO_ATTENTION_BACKEND`.
- Streaming or OpenAI tests hang: prefer unit/TestClient tests and avoid manual
  long-lived server launches unless the task is explicitly operational.
