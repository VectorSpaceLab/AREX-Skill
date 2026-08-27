---
name: pyrit
description: "Use Microsoft PyRIT for generative-AI red teaming, prompt targets,
  scorers, converters, datasets, attack scenarios, scanner CLI, backend, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyRIT repo skill

Use this skill when a task names PyRIT, `pyrit_scan`, `pyrit_backend`, CoPyRIT, Python Risk Identification Tool, AI red teaming, LLM robustness testing, prompt targets, scorers, converters, seed datasets, attack techniques, or scenario campaigns.

This skill is for operating PyRIT as a package. It does not authorize live red-team execution against external systems; require explicit user scope, target approval, credentials handling, and data rules before sending prompts to live services.

## First checks

1. Read [references/repo-provenance.md](references/repo-provenance.md) if you need to decide whether this skill is current for a checkout.
2. Read [references/install-configuration.md](references/install-configuration.md) for package install, optional extras, PyRIT home/config, and no-secret import checks.
3. Run [scripts/pyrit_api_smoke.py](scripts/pyrit_api_smoke.py) when you need a no-secret installed-package sanity check.
4. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, optional dependency, credential, CLI/backend, and layer-boundary problems.

## Route by task

| User need | Read |
|---|---|
| Initialize PyRIT, choose `InMemory`/SQLite/Azure SQL, load config/env files, inspect registries/models/output helpers | [setup-memory-core](sub-skills/setup-memory-core/SKILL.md) |
| Build converters, converter stacks, message normalization, seed prompts/datasets, and data/YAML schemas | [converters-datasets](sub-skills/converters-datasets/SKILL.md) |
| Configure prompt targets, target capabilities, scorers, score aggregation/evaluation, auth/rate-limit/model-service troubleshooting | [targets-scorers](sub-skills/targets-scorers/SKILL.md) |
| Choose/configure attacks, executors, attack techniques, scenarios, benchmarks, prompt generators, concurrency/retries/results | [attacks-scenarios](sub-skills/attacks-scenarios/SKILL.md) |
| Use `pyrit_scan`, `pyrit_shell`, `pyrit_backend`, backend REST service, scanner workflows, or CoPyRIT GUI operations | [cli-backend-scanner](sub-skills/cli-backend-scanner/SKILL.md) |

## Safe operating defaults

- Prefer no-secret import/signature checks before running examples or scans.
- Prefer offline components (`TextTarget`, rule scorers, offline converters, in-memory/temporary SQLite memory) for smoke tests.
- Treat OpenAI/Azure/HuggingFace/LiteLLM/HTTP/Playwright/Azure SQL paths as credentialed or service-bound.
- Treat GCG, HuggingFace, media, browser, and benchmark paths as optional/heavy unless the user explicitly selects them.
- Keep secrets out of prompts, command lines, logs, generated examples, and persisted memory unless the user explicitly authorizes the storage location.

## Minimal Python check

```python
import pyrit
print(pyrit.__version__)
from pyrit.converter import Base64Converter
from pyrit.prompt_target import TextTarget
from pyrit.score.true_false.substring_scorer import SubStringScorer
```

For deeper checks, run the bundled scripts in the relevant sub-skill. They are designed to work from any directory where PyRIT is installed and do not depend on the original repository checkout.
