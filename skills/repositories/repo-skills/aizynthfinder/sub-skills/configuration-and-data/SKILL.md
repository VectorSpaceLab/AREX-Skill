---
name: configuration-and-data
description: "Create, validate, and troubleshoot AiZynthFinder configuration
  files, stocks, model assets, public-data setup commands, and data-tool
  commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Configuration and Data

Use this sub-skill when the task is about AiZynthFinder YAML configuration, data assets, stock files, policy/filter model references, or the bundled data-preparation CLIs. Stay in this sub-skill for safe static validation and setup guidance; route out before running retrosynthesis or interpreting output.

## Owns

- Creating and reviewing YAML sections: `search`, `post_processing`, `expansion`, `filter`, `stock`, and optional `scorer`.
- Explaining env-var interpolation with `${VAR}` and the failure mode for missing variables.
- Choosing short-form versus full-form syntax for expansion policies, filter policies, and stocks.
- Documenting search defaults, `algorithm_config`, bond controls, post-processing keys, and stock stop criteria.
- Preparing asset guidance for model checkpoints, template tables, HDF5/CSV/text stocks, MongoDB stocks, and molbloom stocks.
- Giving safe recipes for `smiles2stock` and `download_public_data` without executing downloads, Mongo writes, or bloom creation unless explicitly requested.
- Running the bundled static validator script to catch schema-shape issues and missing local file references before a search run.

## Routes

- Use [planning-workflows](../planning-workflows/SKILL.md) to execute `aizynthcli`, `aizynthapp`, or an actual retrosynthesis run from a config.
- Use [route-analysis](../route-analysis/SKILL.md) to inspect outputs, route trees, statistics, clustering, or solved-route quality.
- Use [extension-and-development](../extension-and-development/SKILL.md) to implement custom expansion strategies, stock query classes, scorers, filters, plugins, or custom search algorithms.

## References

- [Configuration reference](references/configuration.md) covers YAML sections, defaults, env vars, policy/filter/stock syntax, and validation expectations.
- [Stocks and assets](references/stocks-and-assets.md) covers model/template/stock file formats, optional dependencies, and service assumptions.
- [CLI tools](references/cli-tools.md) covers safe `smiles2stock` and `download_public_data` recipes and when commands mutate external state.
- [Troubleshooting](references/troubleshooting.md) covers common configuration, data, optional dependency, and service failures.

## Safe Validation

Before running a user-provided config, run the bundled validator from any working directory:

```bash
python skills/aizynthfinder/sub-skills/configuration-and-data/scripts/validate_aizynth_config.py path/to/config.yml --json
```

The validator intentionally does not import AiZynthFinder and does not load models, templates, stocks, MongoDB, TensorFlow servers, molbloom filters, or run tree search. Treat `errors` as blockers and `warnings` as setup issues to review with the user.

## Operating Rules

- Keep public guidance asset-agnostic: use user-provided or project-relative paths, not local checkout paths or environment prefixes.
- Do not claim MongoDB, molbloom, TensorFlow serving, public downloads, or route-distance features work until the user confirms the needed optional dependencies and services.
- Do not execute `download_public_data`, Mongo writes, or molbloom creation without explicit user intent because they can use network, storage, or external services.
- If a config validates statically but no expansion policy will be selected during planning, route to planning-workflows for the runtime selection step.
