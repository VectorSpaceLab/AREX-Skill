---
name: prompt-workflows
description: "Compose, validate, and apply reusable Outlines prompt workflows
  with Template, Application, Chat, multimodal inputs, caching, and safe
  iterative prompting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Prompt Workflows

Use this sub-skill when the task is to build or troubleshoot reusable prompt composition around Outlines rather than to choose a model backend or design a schema. It covers:

- Jinja prompt rendering with `outlines.Template`.
- Reusable `outlines.Application` objects that pair a template or callable with an optional output type.
- `outlines.inputs.Chat` conversations and multimodal `Image`, `Audio`, and `Video` inputs.
- Prompt/workflow caching controls.
- Bounded iteration patterns such as structured extraction refinement, self-consistency, task-list loops, and regex-guided structured-output debugging.

Do **not** call remote providers, start local model downloads, or execute model-generated code from this skill alone. After prompt/input assembly is validated, route execution to the appropriate sibling skill: `../structured-generation/` for schemas and output types, `../remote-providers/` for hosted model capability/credential routing, or `../local-models/` for local model setup and capability routing.

## Quick Route

1. **Render first.** Use `Template.from_string(content, filters={})` for inline prompts. Use `Template.from_file(path, filters={})` only when the template file and all includes/extends are bundled under the same template directory boundary.
2. **Fail early on variables.** Outlines templates use Jinja `StrictUndefined`; render with a complete variable mapping before any model call.
3. **Package repeated tasks.** Use `Application(template_or_callable, output_type=None)` when the same prompt/output contract will be applied repeatedly. Call it as `application(model, {"var": value}, **inference_kwargs)`.
4. **Choose the right input carrier.** Import chat and assets from `outlines.inputs`: `Chat`, `Image`, `Audio`, `Video`. Keep each chat message shaped as `{"role": "system"|"user"|"assistant", "content": ...}`.
5. **Validate assets before routing.** `Image` requires a PIL image with a real `format` and base64-encodes it. `Audio` and `Video` are wrappers; actual support is model/provider-specific.
6. **Control caching deliberately.** Use `OUTLINES_CACHE_DIR`, `outlines.caching.cache`, `cache_disabled()`, `outlines.disable_cache()`, and `outlines.clear_cache()` for deterministic workflow components and stale-cache recovery.
7. **Keep iteration bounded and safe.** Self-consistency and agent-loop patterns should have fixed budgets, deterministic parsers, no credential assumptions, no network requirements unless separately authorized, and no `eval`/`exec` of generated code.

## Load These References

- [`references/api-reference.md`](references/api-reference.md): exact APIs, imports, Jinja filters, `Application`, `Chat`, multimodal inputs, and cache controls.
- [`references/workflows.md`](references/workflows.md): reusable workflow recipes distilled from Outlines examples without source-checkout dependencies.
- [`references/troubleshooting.md`](references/troubleshooting.md): failure modes for missing variables, include boundaries, paths, chat/content shape, image/base64 conversion, provider capability mismatches, cache behavior, and generated-code safety.

## Bundled Script

Use [`scripts/render_template.py`](scripts/render_template.py) to render an inline Outlines `Template` with JSON variables or a small built-in fixture before wiring a prompt into an `Application`, `Chat`, or generator call. The script performs only local template rendering; it does not read repository-relative prompt files by default, call providers, or execute generated code.

Example:

```bash
python scripts/render_template.py \
  --template 'Hello {{ name }}!' \
  --vars-json '{"name":"Ada"}'
```

Expected output:

```text
Hello Ada!
```
