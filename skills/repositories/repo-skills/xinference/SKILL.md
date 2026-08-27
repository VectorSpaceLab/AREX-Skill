---
name: xinference
description: "Use Xinference for local and distributed model serving, Python
  clients, OpenAI-compatible APIs, model backend selection, and production
  operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Xinference

Use this repo skill when a task involves self-hosting, operating, or integrating
Xinference / Xorbits Inference as a model-serving package. It covers the public
CLI, local and distributed service patterns, Python clients, OpenAI-compatible
HTTP APIs, model family registration, optional runtime backends, and operator
configuration.

## First checks

1. Confirm the installed package and console entry points:

   ```bash
   python scripts/check_xinference_install.py --run-cli-help
   ```

2. Inspect public client signatures and entry points when a task depends on API
   arguments or when a checkout may have changed:

   ```bash
   python scripts/inspect_xinference_interfaces.py
   ```

3. Read `references/repo-provenance.md` before deciding whether this skill is
   current for a different checkout or release.

## Route by task

| Task shape | Read next |
| --- | --- |
| Start `xinference-local`, build `xinference launch` commands, stop/list/cache/register models, or plan supervisor/worker clusters | `sub-skills/serving-and-cli/SKILL.md` |
| Use `Client`, `AsyncClient`, cURL, OpenAI SDK base URLs, streaming, embeddings, rerank, image/audio/video requests, or request-shape troubleshooting | `sub-skills/client-and-api/SKILL.md` |
| Choose a model family/backend/extra, validate custom model JSON, reason about LoRA, virtual environments, model format, quantization, or memory estimates | `sub-skills/models-and-backends/SKILL.md` |
| Configure auth, API keys, OIDC, audit, metrics, logging, persistence, frontend static serving, Docker/Kubernetes, IP restrictions, or deployment hardening | `sub-skills/operations-and-security/SKILL.md` |
| Diagnose install/import failures, editable source builds, optional dependency conflicts, frontend build surprises, or cross-cutting package errors | `references/troubleshooting.md` and `references/installation-and-environment.md` |

## Install and environment rules

- Supported Python range is `>=3.10`; match the project’s current packaging
  constraints before selecting an interpreter.
- Basic install uses `pip install xinference`. Select optional extras only for
  the model families/backends actually needed by the task; do not install `all`
  or every backend as a first response.
- In editable source checkouts, set `NO_WEB_UI=1` when you only need Python
  package inspection or backend-free tests and do not want the Web UI build.
- Real model launch may download weights, create per-model virtual environments,
  need extra packages, and require CPU/GPU/MPS/vendor hardware. Treat install
  and import success as a package-surface check, not proof that every model
  backend runs.
- Keep endpoint roles distinct: the Xinference service endpoint is usually the
  root URL, while OpenAI-compatible clients use the same service plus `/v1`.

## Bundled root references

- `references/installation-and-environment.md` explains install variants,
  optional extras, source-build behavior, and safe package checks.
- `references/troubleshooting.md` covers cross-cutting package, dependency,
  cache, frontend, auth-header, and model-download symptoms.
- `references/repo-provenance.md` records the source snapshot and refresh
  baseline.
- `references/repo-routing-metadata.json` is structured metadata for managed
  `repo-skills-router` import; do not edit router Markdown by hand.

## Bundled root scripts

- `scripts/check_xinference_install.py` checks importability, distribution
  metadata, client aliases, and console entry point availability without
  starting services.
- `scripts/inspect_xinference_interfaces.py` prints verified public signatures
  for clients, model handles, and selected API helpers.

## Safety and non-goals

- This skill is self-contained. Do not require future agents to open original
  repo docs, tests, examples, scripts, or checkout paths.
- Do not claim that vLLM, SGLang, MLX, image, audio, video, or real model
  inference was verified unless a later verification run actually exercised
  that backend and model.
- Do not print or store real API keys, JWT secrets, encryption keys, OIDC
  client secrets, or model-hub tokens in examples or generated commands.
- Use placeholders for hosts, ports, model UIDs, model names, paths, API keys,
  and worker addresses until the user provides deployment-specific values.
- For repository editing or CI development tasks, use the project’s maintainer
  guidance separately; this operating skill is for package/service use by a
  later Researcher.
