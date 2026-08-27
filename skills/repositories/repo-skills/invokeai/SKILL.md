---
name: invokeai
description: "Route InvokeAI server operations, node workflow authoring,
  workflow queue records, and model-management diagnostics for future coding
  agents."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# InvokeAI Repo Skill

Use this repo skill when a task names InvokeAI or asks about its Python server, CLI, node workflow system, workflow library/queue APIs, model manager, or model/backend diagnostics. InvokeAI is a Python image-generation application and local web server with workflow/node authoring, model records/install/load/cache services, and multiuser/API operations.

## Minimal Setup

- Use Python `>=3.11,<3.13` and install the public package or local checkout with the backend extras appropriate for the task.
- For metadata-only work, first verify the lightweight import surface with `python -c "import invokeai, invokeai.version; print(invokeai.version.__version__)"`.
- Do not treat a metadata-only import as proof that server startup, Torch/diffusers backends, model loading, or generation workflows are ready.

## Start Here

- Read `references/environment-and-install.md` for package metadata, Python/backend expectations, entry points, backend install choices, and safe import checks.
- Read `references/troubleshooting.md` for cross-cutting install/import/runtime/backend guidance before running heavyweight operations.
- Read `references/repo-provenance.md` before deciding whether this skill is stale for a checkout.
- Use `scripts/check_invokeai_skill_assets.py` to verify this skill tree’s bundled references, scripts, frontmatter, and structured metadata.

## Route by Task

- Use `sub-skills/operations-config/SKILL.md` for `invokeai-web`, root/config resolution, env/YAML settings, FastAPI route discovery, OpenAPI/auth/user administration, and operational startup issues.
- Use `sub-skills/workflow-nodes/SKILL.md` for custom invocation/node authoring, `invokeai.invocation_api`, field metadata, `InvocationContext`, graph edges, iterator/collector/if behavior, and execution-state semantics.
- Use `sub-skills/workflows-queues/SKILL.md` for workflow library records, bundled default workflow JSON, session queue APIs, batch enqueue payloads, queue privacy redaction, workflow thumbnails, and public/private workflow behavior.
- Use `sub-skills/model-management/SKILL.md` for model taxonomy, records/install/register/import/delete/search, model load/cache diagnostics, LoRA/GGUF/quantization triage, external provider model records, and safe metadata inspection.

## Common Decisions

- Prefer safe metadata, JSON, parser, and `--help` checks before starting the web server, importing all backends, loading model weights, downloading models, or mutating model/user/workflow databases.
- Treat full generation/regression scripts, GPU stress checks, downloads, model conversions, and destructive cleanup as opt-in operations that need explicit user approval and a disposable root or model store.
- Keep workflow JSON, invocation graph execution state, and model records separate: workflow files are frontend/library records, queued sessions hold serialized graph execution state, and model records point to model files/provider sources.
- For multiuser questions, combine `operations-config` for auth setup with `workflows-queues` for workflow/queue owner/public/admin behavior.
- For default workflow compatibility, combine `workflows-queues` for JSON/library structure, `workflow-nodes` for node/edge schemas, and `model-management` for model identifiers and loader compatibility.

## Verification Notes

- The bundled scripts are intentionally lightweight and safe by default. They validate structure, metadata, settings catalogs, route families, and file headers; authoritative runtime checks may still require a complete InvokeAI environment.
- The generated skill does not bundle model weights, frontend assets, Docker images, native tests, or original repo scripts that perform network, GPU-heavy, release, or destructive operations.
