---
name: music-agent-workflows
description: "Configure and operate Muzic MusicAgent safely: install
  prerequisites, manage model and cache layout, validate config, launch CLI or
  Gradio, and troubleshoot tool selection and secrets."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Music Agent Workflows

Use this sub-skill when the request is about MusicAgent itself: setup, configuration, model and download layout, startup, tool enablement, or runtime troubleshooting.

## Start here

- [Setup and configuration](references/setup-and-configuration.md)
- [Tool and runtime map](references/tool-and-runtime-map.md)
- [Troubleshooting](references/troubleshooting.md)
- [Config validator](scripts/validate_musicagent_config.py)

## What it covers

- Docker vs Conda/pip installation trade-offs.
- Linux system packages needed for audio, notation, and model download support.
- `config.yaml` fields, `local_fold`, `src_fold`, `log_file`, and secret handling.
- CLI vs Gradio launch paths and their credential differences.
- Task planning, tool selection, and model/tool enablement boundaries.
- Safe config validation without importing the source repo.

## What it does not cover

- ROC, DiffSinger, DDSP, and other tool internals.
- Generic provider or gateway policies outside MusicAgent.
- Training or algorithm-level guidance for the wrapped models.

## Operating notes

- Keep API keys, tokens, and `.env` contents out of version control.
- Run MusicAgent from the project directory that contains `config.yaml` so relative paths resolve as expected.
- Not every planner task has a loaded pipe. Some task names are aspirational and will fall through to an "unloaded models" error until the plugin layer is extended.
- If a task fails, check `disabled_tools`, then the `local_fold` cache, then the required system package or credential.
- Use the bundled validator before trying to launch the agent.
