---
name: paddlehelix
description: "Route PaddleHelix tasks across pahelix core APIs,
  compound/drug-discovery workflows, protein sequence/function workflows,
  HelixFold structure prediction, and LinearRNA usage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PaddleHelix

Use this repo skill when a task mentions PaddleHelix, `pahelix`, HelixFold, HelixDock, LinearRNA, PaddlePaddle bio-computing examples, molecular property prediction, DTI, molecular generation, protein sequence/function workflows, or biomolecular structure prediction from this project.

## Start Here

1. Classify the request by workflow domain before opening detailed references.
2. For package/API questions, first check whether the user needs the reusable `pahelix` layer or an app-level workflow.
3. For any training, docking, structure prediction, database download, model-weight download, GPU/DCU run, or environment mutation, validate inputs and ask for explicit execution approval before running heavyweight commands.
4. Use bundled validators and checkers for safe local preflight checks; they do not download data, train models, run GPU inference, or require the original PaddleHelix checkout unless an optional `--repo-root` is explicitly supplied.
5. Read `references/repo-provenance.md` before deciding this skill is current for a checkout, and read `references/troubleshooting.md` for cross-cutting install/import/build/backend failures.

## Route by Task

- Core `pahelix` APIs, `InMemoryDataset`, NPZ caches, splitters, `ProteinTokenizer`, compound utility orientation, featurizer/model-zoo orientation, and import diagnostics: `sub-skills/core-api-data/SKILL.md`.
- Compound representation learning, molecular property prediction, drug-target interaction, molecular generation, drug synergy, few-shot property workflows, HelixDock, and chemistry data/config validation: `sub-skills/compound-drug-discovery/SKILL.md`.
- Protein sequence pretraining/prediction, protein function prediction apps, PPI routing, HelixProtX orientation, FASTA/plain sequence validation, and protein tokenizer/model guidance: `sub-skills/protein-sequence-function/SKILL.md`.
- HelixFold, HelixFold-Single, HelixFold3, HelixFold-S1, biomolecular input JSON, MSA/database/checkpoint requirements, precision choices, and structure-prediction output planning: `sub-skills/structure-prediction/SKILL.md`.
- LinearRNA, LinearFold, LinearPartition, RNA folding constraints, base-pair cutoffs, and missing `linear_rna` extension/build issues: `sub-skills/linear-rna/SKILL.md`.

## Install and Import Orientation

PaddleHelix is distributed as `paddlehelix` and exposes the main Python package as `pahelix`. The source metadata declares version `1.0.0b` and base dependencies including NumPy, pandas, NetworkX, and legacy `sklearn` metadata; modern environments usually need `scikit-learn` installed directly.

Minimal source-layout smoke checks:

```bash
python -c "import pahelix; print(pahelix.__file__)"
python scripts/check_paddlehelix_environment.py --help
```

For core API checks against a local checkout or installed package, use the owning sub-skill checker:

```bash
python sub-skills/core-api-data/scripts/check_core_api.py --check imports --check protein-tokenizer
```

Expect many app workflows to require optional packages and external tools that are not needed for simple API orientation: PaddlePaddle, PGL, RDKit, OpenBabel, MSA binaries, OpenMM/PDBFixer, compatible CUDA/DCU stacks, model checkpoints, databases, and task datasets.

## Safe Bundled Helpers

- `scripts/check_paddlehelix_environment.py`: shared import and optional dependency diagnostic for `pahelix`, package metadata, and common optional modules.
- `sub-skills/core-api-data/scripts/check_core_api.py`: dependency-light core API checks for imports, protein tokenization, dataset cache behavior, splitters, and expected failure simulations.
- `sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py`: local SMILES, JSON config, CSV, and common chemistry/DTI layout preflight.
- `sub-skills/protein-sequence-function/scripts/validate_protein_inputs.py`: FASTA/plain sequence, token IDs, TAPE configs, and protein-function path preflight.
- `sub-skills/structure-prediction/scripts/validate_helixfold3_input.py`: HelixFold3 and HelixFold-S1 entity JSON schema/resource preflight.
- `sub-skills/linear-rna/scripts/check_linear_rna.py`: LinearRNA sequence/constraint validation and optional toy API checks when the extension imports.

Run helpers from their owning skill directories or provide paths explicitly. Do not use these helpers as proof that heavyweight datasets, checkpoints, GPU memory, compiled extensions, or third-party binaries are available unless the helper explicitly checks that surface.

## Capability References

- `references/capability-map.md`: concise mapping from user intent to sub-skill, evidence, bundled helper, and verification candidate.
- `references/troubleshooting.md`: cross-cutting install/import/build/backend/download issues.
- `references/repo-provenance.md`: source snapshot and refresh baseline.
- `references/repo-routing-metadata.json`: structured router metadata used during managed DisCo import.

## Safety and Scope

- Do not run original PaddleHelix app launchers, reproduce scripts, notebooks, download scripts, or training/inference commands by default; use the bundled references to construct a plan and confirm side effects first.
- Do not assume the lightweight inspection environment can execute app workflows; it verifies source/package orientation and documents optional dependency failures.
- Treat `competition/` and `research/` as long-tail evidence only unless the user explicitly asks for those historical experiments.
- If a current checkout differs from the provenance commit, dirty state, package metadata, or evidence paths, refresh this skill before relying on it for detailed routing.
