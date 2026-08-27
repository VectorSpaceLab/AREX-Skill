---
name: openllm
description: "Guides OpenLLM installation, model catalog management, local
  OpenAI-compatible serving, BentoCloud deployment, and operational
  troubleshooting for self-hosted LLM workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenLLM Repo Skill

Use this skill when a task asks about **OpenLLM** or about running open-source LLMs through an OpenAI-compatible local server, terminal chat, custom model repositories, or BentoCloud deployment with the `openllm` CLI.

OpenLLM is a Typer-based Python CLI. Its public entry point is `openllm`, and the package distribution is `openllm`.

## Fast install and import check

For ordinary use, install the package from PyPI:

```bash
python -m pip install openllm
openllm --help
openllm --version
```

For a source checkout, use an editable install in an isolated environment:

```bash
python -m pip install -e .
python -c "import openllm; print(openllm.__name__)"
openllm --help
```

Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this generated skill matches a different checkout or needs refresh.

## Route by task

| Task or signal | Read next |
| --- | --- |
| Start an LLM server, use `/chat`, call the OpenAI-compatible `/v1` API, use `openllm serve`, `openllm run`, or `openllm hello` | [sub-skills/local-serving/SKILL.md](sub-skills/local-serving/SKILL.md) |
| List models, inspect a model, update/add/remove model repositories, parse custom repo URLs, or debug missing model catalog entries | [sub-skills/model-repositories/SKILL.md](sub-skills/model-repositories/SKILL.md) |
| Deploy a model to BentoCloud with `openllm deploy`, choose an instance type, pass `--env`, or debug BentoCloud login/context/config | [sub-skills/cloud-deployment/SKILL.md](sub-skills/cloud-deployment/SKILL.md) |
| Diagnose install/import, GPU/resource detection, per-model dependency venvs, cache locations, cleanup commands, or analytics opt-out | [sub-skills/environment-maintenance/SKILL.md](sub-skills/environment-maintenance/SKILL.md) |
| Need a one-page root command map | [references/cli-overview.md](references/cli-overview.md) |
| Cross-cutting install, network, credentials, hardware, or cache failures | [references/troubleshooting.md](references/troubleshooting.md) |

## Core CLI families

```bash
openllm hello                 # interactive starter that updates model repos and suggests run/serve/deploy
openllm serve MODEL[:VERSION] # local OpenAI-compatible server and browser chat UI
openllm run MODEL[:VERSION]   # local server plus terminal chat loop
openllm deploy MODEL[:VERSION]# deploy to BentoCloud
openllm model list|get        # inspect available Bentos/models
openllm repo list|add|remove|update|default
openllm clean ...             # remove model, repo, venv, or config caches; some commands are destructive
```

OpenLLM model serving is model-specific: full serving may require a model repository cache, model downloads, per-Bento dependencies, Hugging Face credentials for gated models, and enough GPU/CPU resources. Use this skill's dry-run helpers and troubleshooting references before starting long-running downloads or deployments.

## Safe bundled helpers

- Run [scripts/check_openllm_install.py](scripts/check_openllm_install.py) to check Python importability, distribution version, CLI availability, and optional NVIDIA GPU visibility without starting a model.
- Use sub-skill scripts for workflow-specific dry runs, command planning, local catalog inspection, and resource estimation.

## Boundaries

This is an operating skill for using OpenLLM as a package and CLI. It is not a guide to editing OpenLLM's release automation, pushing tags, or mutating the original repository. Do not run cleanup, deployment, repository cloning, or model download commands unless the user explicitly asks for that side effect and understands the credentials/network/storage implications.
