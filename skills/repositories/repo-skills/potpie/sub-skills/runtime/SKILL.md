---
name: runtime
description: "Operate Potpie setup, daemon, backend, status, UI, and telemetry workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Potpie runtime

Use this sub-skill when the task is about getting Potpie installed, initialized, reachable, or diagnosed before any graph, source, auth, or skill-management work.

## Read this when

- The user asks about `potpie setup`, `potpie status`, `potpie doctor`, `potpie whoami`, `potpie config`, `potpie ui`, `potpie daemon`, `potpie backend`, or `potpie telemetry`.
- A command reports `unavailable`, `daemon not running`, backend startup problems, or missing install state.
- You need a safe smoke check for the installed package or the public context APIs.

## Do not use this for

- Pot/source tenancy and repo binding: read `../workspace-boundaries/SKILL.md`.
- Provider credentials or ledger binding: read `../auth-integrations/SKILL.md`.
- Graph reads or writes: read `../graph-read/SKILL.md` or `../graph-write/SKILL.md`.
- Installing Potpie's bundled agent skills: read `../skills-management/SKILL.md`.

## Operating procedure

1. Confirm the CLI is available: `potpie --version` and `potpie --help`.
2. For published usage, prefer `uv tool install potpie` or `python -m pip install potpie`. In a live source checkout, the repo Makefile also exposes `make cli-install` and `make cli-status`.
3. Check runtime readiness with `potpie daemon status` first. It is safe when the daemon is stopped and distinguishes detached daemon state from package import failure.
4. Use `potpie setup --dry-run` before first-run mutations when you need to preview repo binding, agent-skill installation, or host-mode choices.
5. Treat `potpie status`, `potpie doctor`, `potpie backend list`, and `potpie skills status` as daemon-dependent. If they report unavailable while `daemon status` says `up=False`, diagnose daemon startup rather than reinstalling the package.
6. Use the bundled root helpers when you need quick checks:
   - `../../scripts/potpie_smoke.sh`
   - `../../scripts/typecheck_public_context_api.py`
   - `../../scripts/generate_agent_contract.py`

## References

- `references/workflow.md` — setup, daemon, backend, UI, telemetry, and smoke-check matrix.
- `references/troubleshooting.md` — install drift, daemon, backend, and telemetry failure handling.

## Verification notes

- Safe native candidates include the root CLI bootstrap/status, install-status, daemon RPC/launcher, UI router, and telemetry CLI unit tests.
- No selected runtime workflow requires GPU or accelerator verification. A CUDA-capable torch wheel may be present, but it is not a required Potpie runtime backend for this skill.
