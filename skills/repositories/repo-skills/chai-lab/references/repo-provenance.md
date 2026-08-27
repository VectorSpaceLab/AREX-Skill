# Repository Provenance

This skill was generated from the Chai Lab / Chai-1 repository as a self-contained repo skill.

## Source Snapshot

- Repository: `chai-lab`
- Public remote: `https://github.com/chaidiscovery/chai-lab`
- Branch: `main`
- Commit: `c544fb183e865c4950909444db860a9d50604f66`
- Exact tag: none recorded
- Package distribution/import: `chai_lab`
- Package version: `0.6.1`
- Working tree state at extraction start: clean
- Working tree state after generation: dirty from generated `skills/` output only

## Evidence Paths

- `pyproject.toml`
- `requirements.in`
- `README.md`
- `chai_lab/__init__.py`
- `chai_lab/main.py`
- `chai_lab/chai1.py`
- `chai_lab/utils/paths.py`
- `chai_lab/data/dataset/inference_dataset.py`
- `chai_lab/data/parsing/fasta.py`
- `chai_lab/data/parsing/input_validation.py`
- `chai_lab/data/parsing/restraints.py`
- `chai_lab/data/parsing/glycans.py`
- `chai_lab/data/parsing/msas/aligned_pqt.py`
- `chai_lab/data/parsing/msas/a3m.py`
- `chai_lab/data/parsing/templates/m8.py`
- `chai_lab/data/dataset/msas/load.py`
- `examples/predict_structure.py`
- `examples/msas/README.md`
- `examples/msas/predict_with_msas.py`
- `examples/templates/predict_with_templates.py`
- `examples/restraints/README.md`
- `examples/restraints/predict_with_restraints.py`
- `examples/restraints/contact.restraints`
- `examples/restraints/pocket.restraints`
- `examples/covalent_bonds/README.md`
- `examples/covalent_bonds/1ac5.fasta`
- `examples/covalent_bonds/1ac5.restraints`
- `examples/covalent_bonds/8cyo.fasta`
- `examples/covalent_bonds/8cyo.restraints`
- `scripts/stage_colabfold_outputs_for_chai.py`
- `tests/test_parsing.py`
- `tests/test_inference_dataset.py`
- `tests/test_colabfold_msas.py`
- `tests/test_msa_a3m_tokenization.py`
- `tests/test_restraints.py`
- `tests/test_glycans.py`
- `tests/test_cif_utils.py`
- `tests/test_rdkit.py`

## Installed Package Inspection

A private inspection environment verified:

- Editable installation of `chai_lab==0.6.1` from the repository snapshot.
- Imports: `chai_lab`, `chai_lab.chai1`, `chai_lab.main`.
- `python -m pip check` with no broken requirements.
- `chai-lab --help`, `chai-lab fold --help`, and `chai-lab a3m-to-pqt --help`.
- Safe smoke checks for `run_inference` signature import and FASTA parsing.

The private environment prefix and local executable path are intentionally omitted from this public provenance file.

## Refresh Guidance

Refresh this skill when any of these change:

- `chai_lab.chai1.run_inference`, `make_all_atom_feature_context`, or `run_folding_on_context` signatures.
- CLI command names or `chai-lab fold` / `a3m-to-pqt` options.
- FASTA header/entity parsing, glycan parsing, restraint CSV schema, or MSA/template formats.
- Download/cache behavior, model component names, or package dependency/backend requirements.
- Public examples, docs, or tests that add new user-facing workflows.
