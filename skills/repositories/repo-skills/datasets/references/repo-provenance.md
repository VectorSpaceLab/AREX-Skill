# Repo Provenance

- Skill id: `datasets`
- Source project: Hugging Face Datasets
- Source commit: `06fcc085fcdd22fc5cc741954f6187dd879543b6`
- Source branch: `main`
- Exact tag: none detected
- Remote URL: https://github.com/huggingface/datasets
- Working tree state at generation: dirty because DisCo-generated files were added under `skills/`
- Package version from metadata and installed inspection: `5.0.1.dev0`
- Python support from package metadata: `>=3.10.0`
- Console entry point: `datasets-cli=datasets.commands.datasets_cli:main`

## Evidence Paths

- `README.md`
- `setup.py`
- `pyproject.toml`
- `src/datasets/`
- `docs/source/`
- `tests/`
- `templates/`
- `notebooks/README.md`

## Excluded Evidence

- `.git/`, `.dvc/`, caches, and generated/build outputs
- `.github/` and maintainer CI configuration
- `benchmarks/` because benchmark workflows are expensive and not part of the selected runtime skill scope
- `utils/release.py` because it is maintainer-only release automation
- `skills/tests/` because it is DisCo review/test artifact output
