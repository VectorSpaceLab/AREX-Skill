# Repository Provenance

schema: `disco.repo-provenance.v1`

## Source Snapshot

- VCS: git
- Commit: `046c8b84fdcbf7e1b72bbbbd07fa2502ff9b94dd`
- Branch: `master`
- Exact tag: none detected
- Remote URL: https://github.com/deepchem/deepchem
- Working tree state at generation: dirty because the generated `skills/` tree was added during this DisCo run
- Package distribution version observed in inspection environment: `2.8.1.dev20260621163742`
- Package import version observed from `deepchem.__version__`: `2.8.1.dev`

## Evidence Paths

- `setup.py`, `setup.cfg`, `README.md`, `requirements/`
- `deepchem/__init__.py`
- `deepchem/data/`, `deepchem/data/tests/`
- `deepchem/feat/`, `deepchem/feat/tests/`
- `deepchem/splits/`, `deepchem/splits/tests/`
- `deepchem/trans/`, `deepchem/trans/tests/`
- `deepchem/molnet/`, `deepchem/molnet/tests/`
- `deepchem/models/`, `deepchem/models/tests/`
- `deepchem/metrics/`, `deepchem/metrics/tests/`
- `deepchem/hyper/`, `deepchem/hyper/tests/`
- `deepchem/dock/`, `deepchem/dock/tests/`
- `deepchem/feat/complex_featurizers/`, `deepchem/feat/material_featurizers/`
- `docs/source/get_started/`, `docs/source/api_reference/`
- `examples/README.md`, representative `examples/data_loading/`, `examples/splitters/`, `examples/delaney/`, `examples/tox21/`, `examples/hyperparam_opt/`, `examples/model_restore/`, `examples/binding_pockets/`, `examples/pdbbind/`, and tutorial notebook names
- `scripts/colab_install.py`, `scripts/install_deepchem_conda.sh`, `scripts/install_deepchem_conda.ps1`, `scripts/light/install_deepchem.sh`

## Scope Notes

Generated guidance focuses on public package usage rather than DeepChem release engineering, Docker images, CI, or legacy `contrib/` experiments. Optional neural, docking, materials, and DFT backends are documented as dependency-gated workflows because the verified inspection environment intentionally installed only base DeepChem dependencies.
