# NNI Root Troubleshooting

Read this when the user reports install, import, package metadata, `nnictl`, optional dependency, or source-build problems before a specific HPO, NAS, compression, or utility route is clear.

## Fast Triage

```bash
python scripts/check_nni_environment.py --format text
python -c "import nni; print(nni.__version__)"
nnictl --help
```

If a task is already clearly in one workflow, use the nearest sub-skill troubleshooting file after this root triage:

- HPO and `nnictl`: `sub-skills/hpo-experiments/references/troubleshooting.md`
- NAS: `sub-skills/nas/references/troubleshooting.md`
- Compression: `sub-skills/model-compression/references/troubleshooting.md`
- Feature engineering/utilities: `sub-skills/feature-engineering-and-utilities/references/troubleshooting.md`

## Installation And Import Failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: nni` | Package not installed in the active Python | Install with `python -m pip install nni`, then rerun the import check in the same Python. |
| Installed checkout fails on missing frontend/node package material | Source tree has not generated packaged frontend assets | For normal usage, install the released package. For source builds, build frontend assets first or restrict the task to Python API inspection. |
| `nnictl` exists in one shell but not another | PATH or Python environment mismatch | Run `python -m pip show nni`, `python -m pip --version`, and `which nnictl`; ensure they belong to the same environment. |
| `ModuleNotFoundError: pkg_resources` from `nnictl` | Newer setuptools no longer provides the legacy API imported by this checkout | Install a compatible setuptools in that environment, for example `python -m pip install 'setuptools<81'`, or use a release that has migrated away from `pkg_resources`. |
| `pip check` reports dependency conflicts | Mixed old/new dependencies or shared environment contamination | Prefer a clean virtual environment; do not repair a user’s shared environment without approval. |

## Optional Dependency Boundaries

Base NNI covers core experiment APIs, `nnictl`, HPO config machinery, and required scientific packages. Many workflows require additional stacks:

| Workflow | Common optional dependencies | Route |
| --- | --- | --- |
| Optional HPO algorithms | `hyperopt`, `ConfigSpace`, `smac4nni`, `statsmodels`, `gym`, `pybnn` | `sub-skills/hpo-experiments/` |
| NAS PyTorch model spaces and evaluators | `torch`, `pytorch_lightning`, benchmark database packages | `sub-skills/nas/` |
| Compression | `torch`, Lightning, Transformers, DeepSpeed, ONNX, TensorRT, PyCUDA depending on workflow | `sub-skills/model-compression/` |
| Feature selectors/utilities | LightGBM, torch, sklearn/scipy/pandas, graph/profiler helpers | `sub-skills/feature-engineering-and-utilities/` |

Do not recommend `nni[all]` as the first repair unless the user explicitly wants most optional algorithms and accepts a larger dependency footprint. Prefer the narrow dependency tied to the failing import or algorithm.

## Runtime And Service Problems

- Local experiments need a valid trial command, trial code directory, search space, tuner/assessor config, idle port, and a Python environment that can import the trial dependencies.
- Remote/cloud training services require credentials, cluster/service reachability, storage configuration, compatible Python/NNI versions on workers, and safe secret handling.
- Full NAS searches, compression training/calibration, notebooks, and benchmarks can be GPU-, data-, or time-heavy. Use bundled static validators and diagnostics first.

## Source-build Caveats

NNI source packaging includes Python modules plus generated Node/Web UI assets. A source checkout can be useful for reading Python APIs even when frontend assets are absent, but a distributable wheel or full editable install may require frontend generation. Keep that distinction clear:

- For user tasks that only need Python API inspection, import `nni` and selected submodules from a prepared environment and mark Web UI assets unavailable.
- For user tasks that need `nnictl create` with Web UI assets, use a proper release install or complete the source frontend build first.
- Do not treat generated frontend files as evidence for HPO/NAS/compression APIs unless the task is specifically about NNI frontend development.
