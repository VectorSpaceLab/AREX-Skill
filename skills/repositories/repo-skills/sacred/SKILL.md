---
name: sacred
description: "Use Sacred to configure, run, log, observe, and reproduce Python
  ML experiments with experiment, configuration, CLI, observer, and
  reproducibility workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sacred repo skill

Use this repo skill when a task involves the Sacred Python package for experiment management: defining experiments, injecting configuration, running command-line variants, recording run metadata, storing artifacts/metrics, or making experiments reproducible.

## Install and import check

Sacred is a Python package. For normal use start with:

```bash
python -m pip install sacred
python - <<'PY'
import sacred
from sacred import Experiment, Ingredient
print(sacred.__version__, Experiment, Ingredient)
PY
```

If importing Sacred fails with `ModuleNotFoundError: No module named 'pkg_resources'`, install a setuptools release that still provides `pkg_resources`:

```bash
python -m pip install 'setuptools<81'
```

Run [scripts/sacred_env_check.py](scripts/sacred_env_check.py) after installation to verify importability, public signatures, a tiny in-process experiment, and optional dependency visibility without external services.

## Route map

- Use [sub-skills/experiment-core/SKILL.md](sub-skills/experiment-core/SKILL.md) to create or refactor Sacred experiments, ingredients, captured functions, commands, programmatic runs, resources, artifacts, and `Run` usage.
- Use [sub-skills/configuration-and-cli/SKILL.md](sub-skills/configuration-and-cli/SKILL.md) to define config scopes/dicts/files, named configs, config hooks, command-line `with` updates, built-in commands, CLI flags, and custom CLI options.
- Use [sub-skills/observers-and-logging/SKILL.md](sub-skills/observers-and-logging/SKILL.md) to attach observers, use `FileStorageObserver`, store metrics/info/resources/artifacts, inspect local run directories, and reason about optional database/cloud/chat observers.
- Use [sub-skills/reproducibility-and-capture/SKILL.md](sub-skills/reproducibility-and-capture/SKILL.md) to control seeds, `_seed`/`_rnd`, dependency/source discovery, clean-repo enforcement, `SETTINGS`, stdout/stderr capture modes, output filters, and TensorFlow summary tracking.

## Shared references

- Read [references/package-overview.md](references/package-overview.md) for package purpose, public surface, optional dependencies, and how the four sub-skills fit together.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, optional dependency, service, and workflow triage before drilling into sub-skill troubleshooting.
- Read [references/repo-provenance.md](references/repo-provenance.md) before refreshing this skill for a different Sacred checkout or version.

## Operating guidance

1. Treat Sacred as an experiment wrapper around user code, not a training framework. The user supplies the ML/data code; Sacred owns configuration, command routing, observation, and reproducibility metadata.
2. Keep experiments deterministic by recording `seed`, using captured `_seed`/`_rnd`, and validating dependency/source capture before comparing runs.
3. For first-time validation, prefer a local `FileStorageObserver` and temporary directories before adding MongoDB, SQL, cloud, chat, or dashboard integrations.
4. Use `print_config`, `print_dependencies`, and the bundled probe scripts as safe checks before launching expensive experiments.
5. Do not assume optional observers or TensorFlow integration are available. Verify packages, services, credentials, and backend versions explicitly.
6. When creating reusable project guidance, copy or adapt Sacred patterns into the target project; do not depend on the original Sacred source checkout.
