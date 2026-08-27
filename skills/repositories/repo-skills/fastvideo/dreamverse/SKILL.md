---
name: dreamverse
summary: Work on the FastVideo Dreamverse app, server, mock server, GPU pool,
  WebSocket/session flow, launch scripts, Docker, and Modal deployment docs.
description: "Use when a task touches apps/dreamverse source, tests,
  launch/deploy scripts, runtime dependency checks, frontend prompt assets, or
  Dreamverse integration with FastVideo streaming/generation."
license: Apache 2.0
metadata:
  disco-role: operating
disable-model-invocation: true
---

# FastVideo Dreamverse

## Activate this subskill for

- `apps/dreamverse/dreamverse/` server, routes, session, GPU pool, prompt,
  safety, logging, runtime, or mock-server code.
- `dreamverse-server` or `dreamverse-mock-server` console script behavior.
- Dreamverse WebSocket/session streaming protocol or UI-facing payload shape.
- `apps/dreamverse/scripts/launch/`, `apps/dreamverse/scripts/modal/`, or
  `apps/dreamverse/docker/` deployment flows.
- Dreamverse prompt/style/LoRA configuration or frontend static/prompt assets.

## Read first

- `apps/dreamverse/AGENTS.md`
- top-level `AGENTS.md`
- `fastvideo/AGENTS.md` and `fastvideo/entrypoints/streaming` docs/tests when
  touching shared streaming behavior
- `apps/dreamverse/README.md`
- `apps/dreamverse/docker/README.md`
- `apps/dreamverse/scripts/launch/README.md`
- `apps/dreamverse/scripts/modal/README.md`
- `docs/design/server_contracts/streaming.md` if protocol compatibility changes

## Code map

- Server app: `apps/dreamverse/dreamverse/main.py`.
- Dependency gate: `apps/dreamverse/dreamverse/_deps.py`.
- Console entry wrapper: `apps/dreamverse/dreamverse/server_entry.py`.
- Mock server: `apps/dreamverse/dreamverse/mock_server.py`.
- Config/model/LoRA/env handling: `apps/dreamverse/dreamverse/config.py`.
- GPU lifecycle: `apps/dreamverse/dreamverse/gpu_pool.py`.
- Runtime singletons: `apps/dreamverse/dreamverse/runtime.py`.
- Session/WebSocket controller: `apps/dreamverse/dreamverse/session/`.
- Routes: `apps/dreamverse/dreamverse/routes/`.
- Prompt enhancement/safety/providers: `apps/dreamverse/dreamverse/prompt_*` and
  prompt asset directories.
- Tests: `apps/dreamverse/dreamverse/tests/`.
- Deployment: `apps/dreamverse/docker/`, `apps/dreamverse/scripts/launch/`,
  `apps/dreamverse/scripts/modal/`.

## Runtime dependency facts

The package exposes console scripts from the root distribution:

- `dreamverse-server`
- `dreamverse-mock-server`

`dreamverse-server` intentionally checks runtime dependencies before starting.
Current dependency gate requires importable `openai` and `cerebras.cloud.sdk`
and prints a user-facing message telling users to install `fastvideo[dreamverse]`
when they are missing.

For source/API inspection, construction verified `dreamverse-server --help` and
`dreamverse-mock-server --help` with base FastVideo plus `openai` and
`cerebras-cloud-sdk`. That is not the same as a full production Dreamverse extra
or Modal deployment. Full deployment may require additional packages and assets,
including packages documented in the `dreamverse` extra and deployment READMEs.

## Operating workflow

1. Classify the change:
   - dependency gate/entrypoint;
   - FastAPI route or health/readiness;
   - WebSocket/session protocol;
   - GPU pool/process lifecycle;
   - prompt enhancement/safety/config;
   - mock server;
   - launch/Docker/Modal deployment docs/scripts;
   - frontend asset or prompt bundle.
2. For app/server code, prefer imports, CLI `--help`, and app/TestClient tests
   before starting an actual server.
3. For GPU pool behavior, inspect process lifecycle and cleanup paths. Avoid
   leaving worker processes alive during tests; rely on existing tests where
   possible.
4. For WebSocket/session payloads, keep compatibility with shared streaming
   contracts and update Dreamverse tests plus any shared `fastvideo/entrypoints`
   tests if the contract changes.
5. For runtime dependencies, keep `_deps.py` messages clear and actionable.
   Missing optional services should fail with the intended user-facing install
   instruction, not a raw import traceback.
6. For deployment scripts/docs, verify shell syntax and safe `--help`/dry-run
   paths if available; do not push Modal/Docker deployments unless explicitly
   requested and credentials/runtime are present.

## Suggested verification commands

Safe checks:

```bash
python -m pip check
dreamverse-server --help
dreamverse-mock-server --help
pytest apps/dreamverse/dreamverse/tests/test_entrypoints.py -q
pytest apps/dreamverse/dreamverse/tests/test_mock_server.py -q
pytest apps/dreamverse/dreamverse/tests/test_gpu_pool.py -q
```

Shared streaming checks when protocol or health behavior changes:

```bash
pytest fastvideo/tests/entrypoints/streaming/test_server.py -q
pytest fastvideo/tests/entrypoints/streaming/test_prompt_providers.py -q
pytest fastvideo/tests/contract/test_dreamverse_shape.py -q
```

Escalate only with explicit budget/credentials:

```bash
# inspect the README first; commands may start real services or deployments
bash apps/dreamverse/scripts/launch/<script>.sh
# Modal/Docker deployment commands from apps/dreamverse/scripts/modal/README.md
# or apps/dreamverse/docker/README.md
```

Before escalation, confirm GPU visibility, model paths, API keys, ports, output
state directory, frontend build/static path, and whether long-running services
may remain active.

## Common pitfalls

- Treating `dreamverse-server --help` as proof that model generation works.
- Installing the root package without Dreamverse runtime deps and expecting the
  server entrypoint to start.
- Running deployment scripts without credentials or without reading their README.
- Changing Dreamverse payload shapes without updating shared streaming contract
  tests.
- Forgetting cleanup of GPU pool subprocesses in tests.
- Confusing mock-server protocol tests with real GPU generation.

## Handoff checklist

Report:

- Dreamverse surface changed;
- runtime dependencies/assets assumed;
- server/mock/shared streaming tests run;
- whether real service/deployment/generation was intentionally skipped;
- exact command for production verification if not run locally.
