---
name: aizynthfinder
description: "Use AiZynthFinder for retrosynthetic planning, configuration,
  route analysis, custom extensions, and focused development workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# AiZynthFinder Repo Skill

Use this skill when a user is working with AiZynthFinder, a retrosynthetic route-finding package for planning molecule syntheses with policy-guided tree search.

## First Steps

1. Confirm the user has AiZynthFinder installed in a Python `>=3.10,<3.13` environment.
2. If the task mentions a config, stock, policy model, template library, public-data bundle, or optional service, start with [configuration-and-data](sub-skills/configuration-and-data/SKILL.md).
3. If the task is to run retrosynthesis or one-step expansion, use [planning-workflows](sub-skills/planning-workflows/SKILL.md).
4. If the task starts from an existing `output.json.gz`, HDF5 output, `trees.json`, checkpoint, route collection, or reaction tree, use [route-analysis](sub-skills/route-analysis/SKILL.md).
5. If the task is about custom scorers, stocks, policies, search algorithms, plugin strategies, hooks, or source edits, use [extension-and-development](sub-skills/extension-and-development/SKILL.md).

## Install and Import Check

For end users, install the public package with base dependencies unless the task needs optional features:

```bash
python -m pip install aizynthfinder
python - <<'PY'
from aizynthfinder.aizynthfinder import AiZynthFinder, AiZynthExpander
print(AiZynthFinder, AiZynthExpander)
PY
```

Use `python -m pip install "aizynthfinder[all]"` only when the task needs optional MongoDB, molbloom, route-distance, timeout, or similar extras. Use TensorFlow/gRPC-related extras only for TensorFlow Serving or remote model workflows.

Run [scripts/check_aizynthfinder_env.py](scripts/check_aizynthfinder_env.py) when diagnosing import, version, CLI, or optional-dependency availability without launching a search.

## Sub-Skill Routes

- [planning-workflows](sub-skills/planning-workflows/SKILL.md): build and run `aizynthcli` commands, use `AiZynthFinder` or `AiZynthExpander`, handle single vs batch SMILES, checkpoints, multiprocessing, clustering flags, and GUI/notebook launch decisions.
- [configuration-and-data](sub-skills/configuration-and-data/SKILL.md): write and validate YAML configs, stock files, policy/filter model references, public data commands, `smiles2stock`, `download_public_data`, and optional dependency choices.
- [route-analysis](sub-skills/route-analysis/SKILL.md): inspect `output.json.gz`, HDF5 tables, `trees.json`, checkpoints, `ReactionTree`, `RouteCollection`, route scores, clustering, images, and result summaries.
- [extension-and-development](sub-skills/extension-and-development/SKILL.md): implement or validate custom hooks, stocks, scorers, policies, plugin expansion strategies, search algorithms, and focused source-checkout tests.

## Shared References

- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install, optional dependency, model/stock asset, CLI/API, and backend failures before drilling into sub-skill-specific troubleshooting.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for an AiZynthFinder checkout or should be refreshed.
- `references/repo-routing-metadata.json` is structured metadata used by the managed repo-skills-router during import.

## Routing Guardrails

- Do not run `download_public_data`, MongoDB stock creation, long retrosynthesis batches, GUI launches, or plugin service calls unless the user explicitly asks for those side effects.
- Do not assume user assets exist. Configs normally require a stock file, an expansion policy model, and a reaction template library; filter policies are optional.
- Prefer static validation and CLI/API help checks before running searches with user data.
- Keep optional plugins and service-backed models separate from core install troubleshooting; missing Chemformer, ModelZoo, MongoDB, molbloom, route-distance, or TensorFlow Serving dependencies are feature-specific, not proof that core AiZynthFinder is broken.
