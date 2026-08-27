# AiZynthFinder Cross-Cutting Troubleshooting

Use this reference before a more specific sub-skill troubleshooting page when the symptom could come from installation, optional dependencies, missing chemistry assets, command construction, or service-backed plugins.

## Import or Version Failures

Symptoms:
- `ModuleNotFoundError: No module named 'aizynthfinder'`
- Import succeeds in one shell but not another.
- RDKit, pandas, ONNX Runtime, or Jupyter-related imports fail.

Recovery:
1. Confirm Python is within the supported range: `python --version` should be `>=3.10,<3.13` for this repo version.
2. Run the bundled diagnostic:

   ```bash
   python skills/aizynthfinder/scripts/check_aizynthfinder_env.py --json
   ```

3. Install the base package for core CLI/API tasks: `python -m pip install aizynthfinder`.
4. Add optional extras only when the task needs them; avoid broad extras for simple command construction or output inspection.

## Missing Model, Template, or Stock Assets

Symptoms:
- A config loads but a search cannot begin.
- Expansion policy, filter policy, or stock keys are empty or not selectable.
- File-not-found errors mention model weights, template libraries, masks, stock files, or route-distance models.

Recovery:
1. Use [configuration-and-data](../sub-skills/configuration-and-data/SKILL.md) to validate the config shape and asset paths.
2. Confirm each expansion policy has both a model file and a template file unless it is a documented custom class.
3. Confirm a stock is configured and selected. Core planning usually needs a stock plus at least one expansion policy.
4. Do not run downloads or database writes unless the user has explicitly approved the side effect.

## Optional Dependency Confusion

Feature-specific dependencies are not required for every AiZynthFinder task:

| Feature | Typical requirement | Route |
| --- | --- | --- |
| MongoDB stock | `pymongo` plus a reachable database | [configuration-and-data](../sub-skills/configuration-and-data/SKILL.md) |
| molbloom stock | `molbloom` extra and valid bloom parameters | [configuration-and-data](../sub-skills/configuration-and-data/SKILL.md) |
| Route distance or clustering | route-distance/scientific plotting dependencies and valid route trees | [route-analysis](../sub-skills/route-analysis/SKILL.md) |
| TensorFlow Serving or remote models | TensorFlow/gRPC serving packages and reachable service endpoint | [extension-and-development](../sub-skills/extension-and-development/SKILL.md) |
| Chemformer or ModelZoo plugins | external packages, service/model paths, and plugin config | [extension-and-development](../sub-skills/extension-and-development/SKILL.md) |
| GUI/notebook | Jupyter widgets/notebook stack and an interactive runtime | [planning-workflows](../sub-skills/planning-workflows/SKILL.md) |

## CLI/API Misrouting

Use this rule of thumb:
- `aizynthcli`, `AiZynthFinder`, `AiZynthExpander`, target SMILES, checkpoints, and batch execution belong to [planning-workflows](../sub-skills/planning-workflows/SKILL.md).
- YAML sections, stock/model/template assets, `smiles2stock`, and `download_public_data` belong to [configuration-and-data](../sub-skills/configuration-and-data/SKILL.md).
- Existing output files, route trees, scoring, clustering, images, and summaries belong to [route-analysis](../sub-skills/route-analysis/SKILL.md).
- Custom modules, class paths, plugins, search algorithms, source edits, and focused tests belong to [extension-and-development](../sub-skills/extension-and-development/SKILL.md).

## Safe Escalation

Before running an expensive or side-effecting command, ask whether the user wants it run. Treat these as explicit side effects:
- Downloading public model/data bundles.
- Writing MongoDB stock collections.
- Running long retrosynthesis batches, benchmarks, or notebooks.
- Starting GUI servers, Jupyter sessions, REST services, or TensorFlow Serving.
- Installing broad optional extras or mutating a user-provided environment.
