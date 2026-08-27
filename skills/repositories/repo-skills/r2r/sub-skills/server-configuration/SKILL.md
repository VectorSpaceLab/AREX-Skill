---
name: server-configuration
description: "Use R2R install, serve, config, Docker, provider, and operations workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Server Configuration

Use this sub-skill when the user needs to install or run the R2R server, configure TOML/env values, choose a deployment mode, or troubleshoot startup and provider issues.

## What it owns

- package install and server entry points
- config files, env overrides, and built-in config names
- Docker light/full topology and support services
- provider, logging, maintenance, and operations guidance
- safe diagnostics for server readiness

## Start here

```python
from r2r import get_version
print(get_version())
```

## Route out when the work becomes another topic

- Client usage from Python: `../python-sdk/SKILL.md`
- Document ingestion: `../ingestion-documents/SKILL.md`
- Retrieval/RAG: `../retrieval-rag/SKILL.md`
- Graph workflows: `../graph-workflows/SKILL.md`
- JavaScript client: `../javascript-sdk/SKILL.md`

## Bundled assets

- `references/configuration.md`
- `references/deployment.md`
- `references/provider-and-ops-reference.md`
- `references/troubleshooting.md`
- `scripts/config_probe.py`
