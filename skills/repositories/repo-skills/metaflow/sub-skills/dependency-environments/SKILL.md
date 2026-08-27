---
name: dependency-environments
description: "Guides Metaflow step dependency environments, @pypi, @conda,
  uv/conda modes, package CLI, code packaging, package suffixes, and extension
  loading."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dependency Environments

Use this sub-skill when a task involves `@pypi`, `@conda`, `@pypi_base`, `@conda_base`, `--environment=local|conda|pypi|uv`, package resolution, package suffixes, code package contents, or Metaflow extension/plugin loading.

## Quick Route

- Read [`references/dependency-environments.md`](references/dependency-environments.md) for step and flow dependency decorators, environment modes, and datastore-pinned libraries.
- Read [`references/packaging-and-extensions.md`](references/packaging-and-extensions.md) for `package` CLI, code packages, suffixes, extension loading, and plugin enablement.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for common decorator/environment mismatch and packaging failures.
- Run [`scripts/environment_preflight.py`](scripts/environment_preflight.py) for a read-only environment/plugin diagnostic.

## Minimal Patterns

```python
from metaflow import FlowSpec, pypi, pypi_base, step

@pypi_base(packages={"numpy": "1.26.4"}, python="3.11")
class EnvFlow(FlowSpec):
    @pypi(packages={"pandas": "2.2.2"})
    @step
    def start(self):
        self.next(self.end)
```

Run with a compatible environment mode:

```bash
python flow.py --environment=pypi run
# or
python flow.py --environment=conda run
```

## Boundaries

- Remote compute scheduling belongs in [`../deployment-orchestration/SKILL.md`](../deployment-orchestration/SKILL.md).
- Local flow syntax belongs in [`../flow-authoring/SKILL.md`](../flow-authoring/SKILL.md).
- Repository dev environments and test dependencies belong in [`../repo-maintenance/SKILL.md`](../repo-maintenance/SKILL.md).
