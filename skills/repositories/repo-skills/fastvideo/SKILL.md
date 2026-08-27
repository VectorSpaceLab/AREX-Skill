---
name: fastvideo
summary: Operate in the FastVideo repository for inference/serving,
  model-porting, training, and Dreamverse tasks with backend-aware setup and
  tests.
description: "Use this repo-specific skill when the current task touches
  FastVideo source, examples, tests, docs, scripts, or the Dreamverse app. It
  routes work to the right FastVideo subsystem, preserves the repo's two
  training stacks and per-directory AGENTS rules, and chooses bounded CUDA/test
  verification instead of running heavyweight model jobs by default."
license: Apache 2.0
metadata:
  disco-role: operating
disable-model-invocation: true
---

# FastVideo Repo Skill

## What this skill covers

FastVideo is a GPU-first video generation repository. The stable operating
surfaces are:

- public Python API: `fastvideo.VideoGenerator`, `PipelineConfig`, and
  `SamplingParam`;
- config-first CLI/server entrypoints: `fastvideo generate`, `serve`,
  `router-serve`, `bench`, and `eval`;
- model/config/pipeline registries and model-porting workflows;
- two distinct training stacks: legacy `fastvideo/training/` and modular
  `fastvideo/train/`;
- `apps/dreamverse/` for the Dreamverse demo/server/mock/deployment app;
- CUDA-oriented runtime dependencies, attention backends, and custom kernels.

Use repo-relative paths in user-facing output. Do not assume the construction
host, prepared prefix, GPU count, or private logs are available on a later host.
Construction evidence, if present, lives under
`skills/tests/fastvideo-repo-skill/` and is for audit, not a user runtime
contract.

## First steps on every FastVideo task

1. Read the nearest in-scope `AGENTS.md` before editing any directory.
   Important files include:
   - `AGENTS.md`
   - `fastvideo/AGENTS.md`
   - `fastvideo/configs/AGENTS.md`
   - `fastvideo/models/AGENTS.md`
   - `fastvideo/layers/AGENTS.md`
   - `fastvideo/attention/AGENTS.md`
   - `fastvideo/pipelines/AGENTS.md`
   - `fastvideo/training/AGENTS.md`
   - `fastvideo/train/AGENTS.md`
   - `fastvideo/tests/AGENTS.md`
   - `fastvideo/tests/ssim/AGENTS.md`
   - `scripts/checkpoint_conversion/AGENTS.md`
   - `apps/dreamverse/AGENTS.md` for Dreamverse work.
2. Identify the subsystem before editing. Do not move behavior between
   `fastvideo/training/` and `fastvideo/train/` unless the user explicitly asks.
3. Read the relevant user-facing docs before changing behavior or examples.
4. Pick the smallest verification command that proves the touched surface.
   Heavy generation, SSIM, training, large downloads, deployment, and kernel
   builds require explicit GPU/runtime budget.
5. Run project tools through the project's configured commands. In particular,
   do not bypass pre-commit excludes by shelling out directly to individual
   linters when repo guidance says to use `pre-commit`.

## Route to a subskill

- Inference, generation, public API, CLI/server, OpenAI-compatible endpoints,
  streaming router, or attention backend behavior:
  read `inference-serving/SKILL.md`.
- Adding/adapting a model family, pipeline, config, preset, registry entry,
  checkpoint converter, or local parity test:
  read `model-porting/SKILL.md`.
- Fine-tuning, distillation, datasets, training configs, launch scripts, or
  trainer callbacks/methods/models:
  read `training/SKILL.md`.
- Dreamverse server/UI/mock server, GPU pool, session streaming, Docker/Modal,
  or demo deployment:
  read `dreamverse/SKILL.md`.

If a task crosses categories, load the most specific subskill for the code you
will edit first, then load the second subskill only for its verification or
integration boundary.

## Setup baseline

Follow current repository docs, especially `README.md` and
`docs/getting_started/installation.md`. The documented editable install style is
backend-aware, for example:

```bash
UV_TORCH_BACKEND=cu126 uv pip install -e ".[dev]"
```

Use the CUDA backend that matches the host and docs (`cu126` or `cu130` in the
current docs). For inspection-only or runtime-only tasks, a narrower editable
install can be enough, but do not claim generation/training/backend coverage
from a CPU-only import.

Useful safe probes after install:

```bash
python -m pip check
python - <<'PY'
import fastvideo, torch
from fastvideo import VideoGenerator, PipelineConfig, SamplingParam
print(fastvideo.__version__)
print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
print(VideoGenerator, PipelineConfig, SamplingParam)
PY
fastvideo --help
fastvideo generate --help
fastvideo serve --help
fastvideo router-serve --help
```

This skill also ships `scripts/verify_fastvideo_runtime.py`, a lightweight helper
for import/signature/CLI/CUDA probes.

## Verification ladder

Prefer this order unless the task's own docs or tests require more:

1. Syntax/import/signature checks for the edited modules.
2. Parser/config/registry unit tests that do not download models.
3. CLI `--help` or config-translation tests.
4. Mock/server contract tests that do not start long-lived production services.
5. Targeted GPU smoke only when backend behavior is touched.
6. Model generation, SSIM, training, or local parity suites only after confirming
   model assets, credentials, GPU memory, runtime budget, and expected outputs.

Representative commands:

```bash
pytest fastvideo/tests/api/test_cli_translation.py -q
pytest fastvideo/tests/attention/test_selector_role_override.py -q
pytest fastvideo/tests/entrypoints/test_video_generator.py -q
pytest fastvideo/tests/entrypoints/streaming/test_server.py -q
pytest apps/dreamverse/dreamverse/tests/test_entrypoints.py -q
```

Run SSIM, training, and `tests/local_tests/*` commands only when they match the
actual model/backend task and budget.

## Important boundaries

- `fastvideo-kernel/` has a separate build flow (`cd fastvideo-kernel && ./build.sh`).
  A prebuilt wheel import does not prove source rebuild readiness.
- `FASTVIDEO_ATTENTION_BACKEND` must be set before constructing the generator or
  model components. Do not mutate it mid-process to test multiple backends in
  the same constructed object.
- `fastvideo generate`, `serve`, and `router-serve` are config-first entrypoints;
  prefer config files plus dotted overrides instead of ad-hoc argument surfaces.
- `fastvideo/tests/` is intentionally excluded by the repo's pre-commit config;
  do not bypass that policy with direct formatter/linter calls.
- Dreamverse CLI/import checks are not the same as full Modal/Docker production
  deployment.
- Do not import this skill into a live router or external agent unless the user
  explicitly requests import/export later.
