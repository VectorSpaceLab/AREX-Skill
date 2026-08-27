# Repo Provenance

schema: disco.repo-provenance.v1

## Source Snapshot

- Repository: TIAToolbox
- Public remote: `https://github.com/TissueImageAnalytics/tiatoolbox`
- Branch: `develop`
- Commit: `2560759c6979ad4e82837bfcb03148d6937f5188`
- Exact tag: none recorded
- Working tree state: dirty because the generated `skills/` output tree was untracked during skill creation
- Package distribution: `tiatoolbox`
- Package version: `2.1.2`
- Console entry point: `tiatoolbox=tiatoolbox.cli:main`

## Evidence Paths

Runtime skill content was generated from these relative repo evidence areas:

- `README.md`
- `setup.py`
- `pyproject.toml`
- `requirements/requirements.txt`
- `requirements/requirements_cpu.txt`
- `.github/workflows/pip-install.yml`
- `.github/workflows/python-package.yml`
- `.github/workflows/conda-env-create.yml`
- `docs/installation.rst`
- `docs/pretrained.rst`
- `docs/visualization.rst`
- `docs/usage_examples.rst`
- `docs/jnb_pipelines.rst`
- `docs/algorithms.rst`
- `tiatoolbox/`
- `tiatoolbox/data/pretrained_model.yaml`
- `tiatoolbox/data/remote_samples.yaml`
- `examples/`
- `tests/`

## Included Scope

The skill covers public TIAToolbox usage workflows: WSI I/O, image preprocessing, model inference, annotation/visualization, and CLI/configuration.

## Excluded Scope

The skill intentionally excludes Docker build matrices, benchmark-scale workflows, maintainer-only release/dev tooling, generated caches, and review/test artifacts. These are not user-facing TIAToolbox package workflows.

## Refresh Guidance

Refresh this skill when TIAToolbox changes public CLI commands, model registry keys, reader behavior, preprocessing APIs, model engine signatures, annotation store semantics, visualization data formats, dependency/backend requirements, or examples/tests that define public workflows.
