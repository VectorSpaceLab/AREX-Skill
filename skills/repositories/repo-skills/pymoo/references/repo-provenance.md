# Repo Provenance

## Source snapshot

- Schema: `disco.repo-provenance.v1`
- Repository: `pymoo`
- Public remote: `https://github.com/anyoptimization/pymoo.git`
- Branch at evidence capture: `main`
- Commit: `23110c155aa8f31b5f1b86928227fb3931ba7f00`
- Exact tag at commit: none observed
- Commit date: `2026-07-06 18:34:48 -0700`
- Commit subject: `fix(como_cmaes): restart kernels + guard empty ask; document anytime behaviour`
- Working tree state at source-evidence capture: clean
- Note: generated skill and review artifacts were created afterward under `skills/`; they are not source evidence for this provenance baseline.

## Package baseline

- Distribution/import name: `pymoo`
- Package version from metadata/source: `0.6.2`
- Python requirement: `>=3.10`
- Base dependency families: NumPy/SciPy numerical stack, moocore, autograd, CMA-ES, matplotlib, alive-progress, Deprecated.
- Optional extras observed: `dev`, `parallelization`, `others`, `visualization`, `full`.
- Verified environment handoff status during skill creation: CPU/base package `ok`; optional CUDA/GPU and distributed extras were not required by the selected scope.

## Evidence paths used

Package metadata and root docs:

- `pyproject.toml`
- `setup.py`
- `MANIFEST.in`
- `pytest.ini`
- `README.rst`

Source package:

- `pymoo/optimize.py`
- `pymoo/core/`
- `pymoo/algorithms/`
- `pymoo/problems/`
- `pymoo/operators/`
- `pymoo/termination/`
- `pymoo/constraints/`
- `pymoo/parallelization/`
- `pymoo/functions/`
- `pymoo/indicators/`
- `pymoo/decomposition/`
- `pymoo/mcdm/`
- `pymoo/util/ref_dirs/`
- `pymoo/visualization/`

Documentation evidence:

- `docs/source/installation.md`
- `docs/source/getting_started/`
- `docs/source/interface/`
- `docs/source/problems/`
- `docs/source/constraints/`
- `docs/source/customization/`
- `docs/source/operators/`
- `docs/source/algorithms/`
- `docs/source/parallelization/`
- `docs/source/gradients/`
- `docs/source/misc/`
- `docs/source/mcdm/`
- `docs/source/visualization/`
- `docs/source/api/algorithms.rst`

Examples and tests used as evidence or native candidates:

- `examples/algorithms/`
- `examples/problems/`
- `examples/constraints/`
- `examples/termination/`
- `examples/misc/`
- `examples/visualization/`
- `examples/case_studies/`
- `tests/algorithms/`
- `tests/problems/`
- `tests/operators/`
- `tests/indicators/`
- `tests/misc/`
- `tests/test_decomposition.py`
- `tests/test_api_reference.py`

## Excluded source areas

- VCS, CI, and agent-local infrastructure: `.git/`, `.github/`, `.claude/`, `.pyclawd/`.
- Static/generated documentation assets: static images, templates, generated binary data where not needed for user workflows.
- `pymoo/vendor/` except indirect behavior evidence through public APIs.
- MATLAB examples, benchmark-scale tests, long golden/regression suites, and generated review artifacts.

## Refresh guidance

Refresh this skill when pymoo changes public constructors, algorithm import
paths, problem/constraint conventions, optional extras, visualization APIs,
parallelization runners, or package version. Also refresh if `n_constr`
deprecation behavior changes or optional backend packaging changes materially.
