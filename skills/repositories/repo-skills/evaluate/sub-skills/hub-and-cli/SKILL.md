---
name: hub-and-cli
description: "Create, validate, and publish custom Hugging Face Evaluate
  modules, including evaluate-cli scaffolding, template structure, Hub metadata
  updates, and safe credential/network boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluate Hub and CLI

Use this sub-skill when the task is to author a new custom Evaluate module, inspect `evaluate-cli`, diagnose Hub publishing problems, or update model-card evaluation metadata with `evaluate.push_to_hub`.

Route routine loading or computing of existing modules to `../module-loading/` and `../module-computation/`.

## Safe Entry Points

- Start with `python scripts/inspect_evaluate_cli.py` to check whether the installed CLI imports and exposes help without making network calls.
- Treat `evaluate-cli create ...` as mutating and network-bound: it creates a Hub Space, clones it, renders templates, commits, and pushes.
- Treat `evaluate.push_to_hub(...)` as network-bound: it validates Hub model/dataset information and updates model-card metadata.
- Keep credentialed actions opt-in. Do not run create, push, clone, or login commands unless the user explicitly requests them and confirms token/network availability.

## Authoring Workflow

1. Read `references/creating-modules.md` for module names, `module_type`, scaffolded file responsibilities, `_info`, `_compute`, optional `_download_and_prepare`, README/module-card expectations, tests, and Gradio widget caveats.
2. Read `references/hub-api-reference.md` before using `evaluate.push_to_hub` or explaining metadata fields written to model cards.
3. Read `references/troubleshooting.md` when CLI imports fail, Hub credentials are missing, `module_type` is rejected, hyphenated names are rejected, or widget dependencies fail.
4. For local-only planning, draft the module file, README, requirements, and tests without invoking `evaluate-cli create` or contacting the Hub.
5. For actual publishing, require a logged-in Hugging Face token, an allowed target namespace or organization, and explicit user approval for public/private Space creation.

## Quick Commands

Safe local inspection:

```bash
python scripts/inspect_evaluate_cli.py
python scripts/inspect_evaluate_cli.py --json
```

Credentialed publishing command shape, only after explicit approval:

```bash
evaluate-cli create "My Metric" --module_type metric --organization my-org --private
```

Local module authoring checks are usually safer than publishing checks: inspect generated files, run unit tests for `_compute`, and verify README YAML separately before pushing.

## Evidence

This sub-skill is based on these repository evidence paths: `src/evaluate/commands/evaluate_cli.py`, `templates/`, `docs/source/creating_and_sharing.mdx`, `docs/source/package_reference/hub_methods.mdx`, `src/evaluate/hub.py`, `tests/test_hub.py`, and `src/evaluate/utils/gradio.py`.
