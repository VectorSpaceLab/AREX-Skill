# PaddleHelix Troubleshooting

Read this for failures that cut across multiple PaddleHelix sub-skills. Workflow-specific failures live in the nearest sub-skill `references/troubleshooting.md` or workflow reference.

## Install and Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: pahelix` | The package is not installed and the source root is not on `PYTHONPATH`. | Install the package or run bundled checkers with an explicit `--repo-root` when checking a local source tree. |
| `pip install` fails on deprecated `sklearn` package metadata | Source metadata declares `sklearn`, while modern pip expects `scikit-learn`. | Install `scikit-learn` directly first. Use the legacy compatibility environment variable only when a legacy setup path requires it and the user accepts that workaround. |
| `ModuleNotFoundError: paddle` | PaddlePaddle is optional for lightweight API checks but required for model classes, training, and inference. | Install a PaddlePaddle CPU/GPU package compatible with Python, OS, CUDA/DCU, and the target app before running model workflows. |
| `ModuleNotFoundError: pgl` | Graph dataloaders, many featurizers, and GNN workflows need PGL. | Install PGL compatible with the selected PaddlePaddle version, or route to dependency-light utilities that do not import graph dataloaders. |
| `ModuleNotFoundError: rdkit` | Scaffold splitters and compound graph utilities need RDKit. | Install RDKit before scaffold splitting, molecule parsing, and chemistry feature checks; otherwise use random/index splitters or syntax-only validation. |
| OpenBabel or conversion binary missing | Docking/conversion workflows need external chemistry tools. | Install only for approved HelixDock/conversion workflows; do not install just for core `pahelix` inspection. |

Run the shared checker for a safe summary:

```bash
python scripts/check_paddlehelix_environment.py --help
python scripts/check_paddlehelix_environment.py --optional-modules
```

## LinearRNA Build

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `linear_rna` extension | The CMake/pybind extension was not built or is not importable from the active environment. | Use `sub-skills/linear-rna/scripts/check_linear_rna.py` to validate inputs and import status, then follow `sub-skills/linear-rna/references/build-and-troubleshooting.md`. |
| CMake selects Ninja but no build program is available | Build tooling is incomplete. | Install CMake plus a build tool/compiler appropriate for the platform, then rebuild in a controlled environment. |
| `pybind11` submodule missing | Repository submodules were not prepared. | Prepare submodules only when the user is working in a mutable checkout and approves repository mutation. |

## Data, Config, and Command Safety

- Validate SMILES, JSON configs, CSVs, and common compound/DTI layouts with `sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py` before constructing app commands.
- Validate protein FASTA/plain sequences, TAPE configs, and protein-function path requirements with `sub-skills/protein-sequence-function/scripts/validate_protein_inputs.py`.
- Validate HelixFold3 or HelixFold-S1 entity JSON with `sub-skills/structure-prediction/scripts/validate_helixfold3_input.py` before planning inference.
- Validate LinearRNA sequences and constraints with `sub-skills/linear-rna/scripts/check_linear_rna.py` before API calls.

These validators are preflight tools. They do not prove that model checkpoints, large datasets, MSA binaries, OpenBabel, Paddle GPU, PGL, RDKit, or compiled extensions are installed unless they explicitly check those surfaces.

## Heavy Workflow Boundaries

Do not run these by default:

- Full training, finetuning, distributed jobs, or benchmark-scale app scripts.
- HelixDock reproduce scripts, protein-folding run scripts, database/model download scripts, or notebook workflows.
- GPU/DCU inference, structure-prediction pipelines, MSA generation, OpenMM relaxation, or large docking/conversion jobs.
- Environment mutations such as installing GPU frameworks, rebuilding C++ extensions, or preparing repository submodules.

Instead, use the relevant sub-skill to validate local inputs, identify required dependencies and artifacts, propose a command plan, and ask for explicit approval before side effects.

## Refresh Signals

Refresh this skill when these repository surfaces change:

- `setup.py`, base/optional dependency metadata, package version, or public import names.
- `pahelix/` APIs for datasets, splitters, tokenizers, compound utilities, featurizers, or model-zoo classes.
- App README command contracts, config schemas, data layouts, launch scripts, or requirements files.
- HelixFold3/S1 input JSON schema, run script flags, precision defaults, checkpoint/database layout, or licensing/usage notes.
- LinearRNA binding signatures, build scripts, or CMake/pybind setup.
