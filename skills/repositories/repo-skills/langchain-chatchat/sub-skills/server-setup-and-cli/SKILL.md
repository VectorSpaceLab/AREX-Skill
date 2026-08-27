---
name: server-setup-and-cli
description: "Install, initialize, configure, and start Langchain-Chatchat with
  the chatchat CLI, data root, model providers, and deployment options."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Server Setup and CLI

Use this sub-skill for Langchain-Chatchat installation, `CHATCHAT_ROOT`, YAML configuration, `chatchat init`, `chatchat kb`, `chatchat start`, Docker/Xinference deployment planning, and model-provider setup.

## Read first

- [`references/cli-reference.md`](references/cli-reference.md) lists verified CLI commands and flags.
- [`references/configuration.md`](references/configuration.md) explains `CHATCHAT_ROOT`, generated YAML files, and important settings groups.
- [`references/model-provider-setup.md`](references/model-provider-setup.md) explains provider separation, model names, and Xinference/Ollama/LocalAI/FastChat/One API style configuration.
- [`references/deployment.md`](references/deployment.md) covers pip/source/Docker deployment choices and why AutoDL scripts are not bundled as runnable helpers.
- [`references/troubleshooting.md`](references/troubleshooting.md) gives setup-specific symptoms and recovery steps.
- Run [`scripts/chatchat_config_audit.py`](scripts/chatchat_config_audit.py) against an initialized data root to check expected config/data files without starting services.

## Setup workflow

1. **Choose environment.** Use Python 3.10 or 3.11. Prefer a clean Chatchat environment. Keep heavy model-serving frameworks in separate envs/containers unless the user explicitly wants a combined setup.
2. **Install package.** For normal users, use `python -m pip install -U langchain-chatchat`. For source development, install the server package editable from the server package root.
3. **Pick data root.** Set `CHATCHAT_ROOT` to a persistent directory if the current working directory is not the desired data/config location.
4. **Initialize.** Run `chatchat init` before any service startup. Do not use `--recreate-kb` until embedding provider settings are valid.
5. **Edit YAML.** Update model platform, default LLM, default embedding model, server host/port, KB/vector-store settings, and tool settings as needed.
6. **Rebuild or update KB.** Run `chatchat kb -r` for full vector rebuild only after the embedding model is reachable. Use update/increment/prune flags for lighter maintenance.
7. **Start service.** Use `chatchat start --api`, `chatchat start --webui`, or `chatchat start -a`.
8. **Validate endpoints.** Open API docs at the API service root redirect or use API/SDK probes from sibling sub-skills.

## CLI quick reference

```bash
chatchat --help
chatchat init --help
chatchat kb --help
chatchat start --help
```

Common command sequence:

```bash
export CHATCHAT_ROOT=/path/to/chatchat-data
chatchat init
# edit generated YAML files: model_settings.yaml, kb_settings.yaml, basic_settings.yaml, tool_settings.yaml, prompt_settings.yaml
chatchat kb -r
chatchat start -a
```

If `chatchat kb -r` fails, do not retry blindly. Confirm the embedding provider endpoint and model name first.

## Boundary with sibling sub-skills

- After the API/WebUI process is running, use [`../knowledge-base-and-api/SKILL.md`](../knowledge-base-and-api/SKILL.md) for route payloads, RAG modes, tools, and vector-store API calls.
- Use [`../python-sdk-and-adapters/SKILL.md`](../python-sdk-and-adapters/SKILL.md) for SDK clients, `open_chatcaht`, and LangChain adapter classes.
- Return here when an API/SDK failure points to missing config, wrong model names, `CHATCHAT_ROOT`, provider reachability, or service startup.

## Safety rules

- Do not start Docker Compose, model downloads, or AutoDL process-killing scripts without explicit user approval.
- Do not run `chatchat kb --clear-tables`, prune commands, or `--recreate-kb` against user data until the target `CHATCHAT_ROOT` and backup status are clear.
- Do not claim GPU/provider readiness from package import or CLI help. Provider readiness requires provider-specific checks.
