# CogDL Cross-Cutting Troubleshooting

Use this file for issues that affect the whole package, not just one workflow.
Sub-skill-specific failures still have their own troubleshooting references.

| Symptom | Likely cause | Recovery | Next owner |
| --- | --- | --- | --- |
| `import cogdl` fails immediately | Missing or incompatible PyTorch / runtime dependencies. | Re-check `python -m pip check`, reinstall from a compatible PyTorch environment, and make sure the editable install came from the intended checkout. | Usually `experiments-and-cli` or `models-layers-and-operators` |
| `AttributeError: module 'matplotlib.cm' has no attribute 'get_cmap'` during import | Very new `matplotlib` releases can break the repository's Optuna visualization path. | Pin `matplotlib<3.9` and rerun `python -m pip check`. | `experiments-and-cli` |
| `No broken requirements found` but imports still fail | The package may be importing optional runtime surfaces or a wrong module path is shadowing the install. | Re-run imports from a clean working directory with `python -I`; use `scripts/check_cogdl_environment.py` to inspect the installed package path and registries. | whichever sub-skill owns the failing API |
| Built-in datasets start downloading | The cache is missing and the dataset constructor is doing real work. | Use a custom tiny `Graph` or the bundled graph-data helper, or explicitly approve network/cache writes. | `graph-data-and-datasets` |
| OGB dataset loading fails | `ogb` is absent or the dataset cache is incomplete. | Install `ogb` only if the task really needs that dataset family; otherwise switch to a core dataset or a custom fixture. | `graph-data-and-datasets` |
| OAG-BERT loading attempts to fetch an archive and fails | OAG archives are cache/network resources, and the test archive may not be usable in every environment. | Treat OAG-BERT as optional, confirm the archive/cache, or stop and report the network/cache dependency instead of claiming success. | `pipelines-and-applications` |
| CUDA is visible but not needed | CUDA is optional for this skill tree. | Keep CPU-safe workflows as the baseline; only claim CUDA behavior when a sub-skill explicitly checked it. | `models-layers-and-operators` or `training-wrappers-and-customization` |
| `ninja`, `numba`, or binary wheel problems appear | A compiled dependency or ABI mismatch may have landed in the environment. | Re-run the environment check script, verify `pip check`, and install the minimum compatible dependency set again. | usually `experiments-and-cli` or `models-layers-and-operators` |
| An unknown model, dataset, or app name appears | The task asked for a name that is not in the verified registry. | Use the registry helpers and the relevant sub-skill reference instead of guessing. | `experiments-and-cli`, `models-layers-and-operators`, or `pipelines-and-applications` |

## Recovery sequence

1. Run `python -m pip check` in the target environment.
2. Run `scripts/check_cogdl_environment.py --show-registries`.
3. Identify whether the failure is about data, models, wrappers, pipelines,
   or only the environment.
4. Open the owning sub-skill's troubleshooting file for the workflow-specific
   recovery steps.

## What this file does not cover

- Dataset mask/schema repair: see `sub-skills/graph-data-and-datasets/references/troubleshooting.md`.
- Model/layer/operator build or shape issues: see `sub-skills/models-layers-and-operators/references/troubleshooting.md`.
- Wrapper, checkpoint, logger, or distributed trainer problems: see
  `sub-skills/training-wrappers-and-customization/references/troubleshooting.md`.
- CLI parser, AutoML, or experiment orchestration problems: see
  `sub-skills/experiments-and-cli/references/troubleshooting.md`.
- Pipeline app or OAG-BERT specifics: see
  `sub-skills/pipelines-and-applications/references/troubleshooting.md`.
