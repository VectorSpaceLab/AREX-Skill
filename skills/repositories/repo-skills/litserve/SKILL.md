---
name: litserve
description: "Serve custom AI APIs with LitServe, including general LitAPI and
  LitServer workflows, OpenAI-compatible endpoints, MCP tools, and deployment
  helpers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LitServe

Use this skill when a request mentions LitServe, LitAPI, LitServer, /predict,
/v1/chat/completions, /v1/embeddings, /mcp/, client.py, dockerize, health/info/
shutdown routes, batching, streaming, auth, or multi-endpoint serving.

## Quick install

- Install the package with `pip install litserve`.
- Add optional extras only for the workflow you need: `fastmcp`, `Pillow`,
  `numpy`, `openai`, `httpx`, `asgi-lifespan`, `requests`, `python-multipart`,
  and `psutil`.
- Verify the installation with `scripts/smoke_import.py` or a clean
  `python -I -c "import litserve as ls; print(ls.__version__)"` check.

## Route map

| Task family | Read first |
| --- | --- |
| General serving, deployment, payloads, auth, middleware, clients, Docker | `sub-skills/server-basics/SKILL.md` |
| OpenAI-compatible chat completions and embeddings | `sub-skills/openai-specs/SKILL.md` |
| MCP tool exposure and streamable HTTP mounting | `sub-skills/mcp/SKILL.md` |

## Reference map

- [references/installation.md](references/installation.md): read for install
  options, optional extras, and smoke checks.
- [references/troubleshooting.md](references/troubleshooting.md): read for
  package-wide import, CLI, payload, auth, and deployment failures.
- [references/repo-provenance.md](references/repo-provenance.md): read when you
  need the source snapshot and staleness baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json):
  structured metadata for repo-skills-router import.
- [scripts/smoke_import.py](scripts/smoke_import.py): run to print the import
  smoke report and core signatures.
- [scripts/smoke_server.py](scripts/smoke_server.py): run to launch the bundled
  minimal server and verify one request end to end.

## Shared notes

- The root skill is a router. Detailed workflows, validation tables, and
  troubleshooting belong in the subskills and bundled references.
- Do not point runtime instructions back to source-checkout paths.
- Prefer the root smoke script and the bundled subskill scripts before reopening
  the original repository.

## Good starting questions

- How do I serve a custom model or pipeline?
- How do I add batching, streaming, auth, or middleware?
- How do I expose an OpenAI-compatible chat or embedding endpoint?
- How do I expose an MCP tool from a LitAPI?
- How do I package a LitServe app for Docker or local deployment?
