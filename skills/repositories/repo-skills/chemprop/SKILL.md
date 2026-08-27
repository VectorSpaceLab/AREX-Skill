---
name: chemprop
description: "Use Chemprop 2.2.3 for molecular property prediction: CLI
  training, prediction, fingerprints, data validation, Python APIs,
  reaction/atom-bond tasks, uncertainty, hpopt, and conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Chemprop

Use this skill when working with Chemprop 2.2.3, a Python package and CLI for molecular property prediction with message passing neural networks. It helps future agents design Chemprop commands, validate molecular data, use trained checkpoints, build Python API workflows, handle reaction and atom/bond tasks, and troubleshoot uncertainty, conversion, and hyperparameter workflows without reopening the original source repository.

## Fast Route

- For `chemprop train` commands, task/loss/metric choices, split handling, config files, ensembles, transfer/foundation flags, or training outputs, use [training-cli](sub-skills/training-cli/SKILL.md).
- For `chemprop predict`, `chemprop fingerprint`, checkpoint/model-path handling, output formats, or learned representations, use [prediction-fingerprints](sub-skills/prediction-fingerprints/SKILL.md).
- For CSV/NPZ validation, SMILES/reaction columns, descriptors, atom/bond features, molecule featurizers, datasets, dataloaders, or split APIs, use [data-featurization](sub-skills/data-featurization/SKILL.md).
- For direct Python API model construction, public `chemprop.data`, `chemprop.models`, `chemprop.nn`, Lightning loops, save/load, metrics, and model components, use [python-api-modeling](sub-skills/python-api-modeling/SKILL.md).
- For reaction, multicomponent, MolAtomBond atom/bond targets, constraints, spectral tasks, and specialized molecular schemas, use [specialized-molecular-tasks](sub-skills/specialized-molecular-tasks/SKILL.md).
- For uncertainty estimation/calibration/evaluation, Ray Tune hpopt, conversion, transfer/foundation routing, and advanced interpretation workflows, use [uncertainty-advanced](sub-skills/uncertainty-advanced/SKILL.md).

## Start Here

Chemprop exposes one console command with five subcommands:

```bash
chemprop --help
chemprop train --help
chemprop predict --help
chemprop fingerprint --help
chemprop convert --help
chemprop hpopt --help
```

For a minimal training command:

```bash
chemprop train --data-path data.csv --task-type regression --output-dir runs/regression_demo
```

For a minimal prediction command:

```bash
chemprop predict --test-path test.csv --model-paths runs/regression_demo/model_0/best.pt --output preds.csv
```

For a minimal fingerprint command:

```bash
chemprop fingerprint --test-path test.csv --model-paths model.pt --ffn-block-index 0 --output fps.csv
```

## Installation And Environment Checks

Chemprop 2.2.3 requires Python `>=3.11,<3.15`. Core dependencies include PyTorch, Lightning, RDKit, NumPy, pandas, scikit-learn, SciPy, astartes, ConfigArgParse, rich, and descriptastorus. Optional workflows require extras:

- `chemprop[hpopt]` for Ray Tune hyperparameter optimization.
- `chemprop[cuik_molmaker]` for optional accelerated molecule featurization where supported.
- Notebook/docs/test extras only when developing or reproducing notebooks/tests.

Use the bundled environment check when an agent needs quick diagnostics:

```bash
python scripts/chemprop_environment_check.py
```

Read [references/package-overview.md](references/package-overview.md) for installed-package facts, registries, CLI modes, and workflow ownership. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/backend, CLI, and data issues. Read [references/repo-provenance.md](references/repo-provenance.md) when deciding whether this skill is stale relative to a newer Chemprop checkout.

## Common Decisions

| User intent | First route | Key checks |
| --- | --- | --- |
| Train a molecular regression/classification model | `training-cli` | CSV header, SMILES/target columns, task type, split design, output directory |
| Predict from an existing checkpoint | `prediction-fingerprints` | model path, matching data schema, output suffix, reaction/multicomponent flags |
| Debug data shape or feature files | `data-featurization` | CSV columns, NPZ row counts, descriptor/feature rank, component index alignment |
| Build Chemprop from Python | `python-api-modeling` | RDKit molecules, datapoints/datasets, predictor/loss compatibility, Lightning trainer |
| Use reaction, multicomponent, or atom/bond tasks | `specialized-molecular-tasks` | reaction mode, multiple SMILES columns, target lists, constraints, `--reorder-atoms` |
| Add uncertainty, hpopt, conversion, or foundation workflows | `uncertainty-advanced` | optional extras, compatible model task, calibration data, conversion featurizer mode |

## Public Runtime Boundaries

This skill is self-contained. It distills Chemprop source, docs, tests, examples, and installed-package inspection into bundled references and helper scripts. Do not require future agents to open the original Chemprop repository for normal usage. If a task asks to modify Chemprop itself, treat this skill as usage guidance and then inspect the active checkout normally.

## Safety Defaults

- Use `--accelerator cpu` and `--num-workers 0` for local smoke tests unless GPU/backends are intentionally selected.
- Prefer explicit `--output-dir`, `--smiles-columns`, `--target-columns`, and `--task-type` in generated commands.
- Start with small `--epochs` for data/schema smoke tests before real training.
- Validate CSV/NPZ shape issues with `sub-skills/data-featurization/scripts/validate_chemprop_tabular_inputs.py` before launching expensive runs.
- Do not run notebook-scale examples, hyperparameter optimization, or training-heavy native tests as quick checks unless the user asks for expensive validation.
