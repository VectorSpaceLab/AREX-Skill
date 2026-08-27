---
name: "exploration"
description: "Guides AppAgent's autonomous exploration and human demonstration
  flows that generate UI documentation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Exploration

Use this sub-skill when the task is to create or refresh the documentation base that AppAgent uses later during deployment.

## What this sub-skill covers
- Autonomous exploration of an Android app.
- Human demonstration capture of a similar task.
- Document generation for UI elements after a demo.
- Output structure under `apps/<app>/demos/`, `apps/<app>/auto_docs/`, and `apps/<app>/demo_docs/`.

## When to route here
- The user wants to "explore" an app.
- The user wants to "teach" AppAgent by demonstration.
- The user needs to regenerate docs for a specific app.
- The user is asking why AppAgent has no documentation base for a target app.

## Read first
- `references/workflows.md` for the autonomous versus human-demo flow.
- `references/troubleshooting.md` for capture, prompt, and doc-generation failures.
- `../../references/configuration.md` when the model backend or output directories need adjustment.
- `../../references/api-reference.md` when you need parser or controller details.

## Bundled script
Use the launcher in this sub-skill instead of trying to reconstruct the source launch sequence yourself:
- `scripts/start_exploration.py`

It accepts an explicit `--mode`, uses subprocess calls rather than shell-string execution, and takes `--repo-root <AppAgent checkout>` when you are not already inside the repository.

## Typical workflow
1. Validate the environment with `../../scripts/check_setup.py --repo-root <AppAgent checkout>` if the host/device status is uncertain.
2. Choose an app name and a writable `root_dir`.
3. Run the bundled exploration launcher in `autonomous` mode or `human` mode.
4. Review the generated docs in `auto_docs/` or `demo_docs/`.
5. If the UI meaning is still wrong, rerun with `DOC_REFINE=true` or manually edit the docs.

## What to keep in mind
- Exploration is interactive and requires a live device and adb.
- The model backend must understand images; text-only backends are not enough.
- `step_recorder.py` and `document_generation.py` are internal steps of the human-demo path.
- `self_explorer.py` is the internal autonomous loop.
- The exact model response format matters because the action parser is strict.

## Common failure signals
- No device found.
- Invalid device size.
- Screenshot/XML capture failure.
- Malformed exploration or reflection response.
- Existing doc entry skipped because the UID already has documentation.

## Useful outputs
- `apps/<app>/demos/<demo_name>/record.txt`
- `apps/<app>/demos/<demo_name>/task_desc.txt`
- `apps/<app>/auto_docs/*.txt`
- `apps/<app>/demo_docs/*.txt`

## Cross-links
- Use `../deployment/SKILL.md` after docs are ready.
- Use `../../references/troubleshooting.md` when the failure is shared across both phases.
