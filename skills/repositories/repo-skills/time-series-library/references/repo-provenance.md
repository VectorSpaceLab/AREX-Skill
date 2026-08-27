# Repo Provenance

- Schema: `disco.repo-provenance.v1`
- Repository: `thuml/Time-Series-Library`
- Remote URL: `https://github.com/thuml/Time-Series-Library.git`
- Commit: `4e938a1767106324dd753b2a44832bf870a0252e`
- Branch: `main`
- Exact tag: none detected
- Working tree state at extraction: clean before generated `skills/` outputs were written
- Package distribution: none detected (`pyproject.toml`, `setup.py`, and `setup.cfg` absent)
- Package version: not declared
- Runtime entry point: source-tree `run.py`
- Generated skill id: `time-series-library`

Evidence used: `README.md`, `README_zh.md`, `CONTRIBUTING.md`, `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `run.py`, `exp/`, `data_provider/`, `models/`, `layers/`, `utils/`, `scripts/`, and `tutorial/TimesNet_tutorial.ipynb`.

Refresh this skill when any of these change materially:

- `run.py` arguments, task names, GPU flag behavior, or setting/output naming.
- `data_provider/` dataset names, local file expectations, or Hugging Face fallback behavior.
- `exp/` train/test loops, metric outputs, checkpoint/result folders, or task semantics.
- `models/` model filenames, optional dependencies, or large-model download/device assumptions.
- `scripts/` benchmark template structure or dataset-specific argument conventions.
- `requirements.txt` or Docker instructions for PyTorch, CUDA, Mamba, Moirai, or large time-series model dependencies.
