# Repo Provenance

- Skill id: `clearml`
- Package distribution/import name: `clearml`
- Package version observed from source metadata: `2.1.9`
- Source VCS: git
- Source commit: `2ae541b42ab1ca07623bee3116dcbe79d499434f`
- Source branch: `master`
- Exact tag: none detected
- Working tree state at generation: dirty because the new generated skill/artifact files were untracked under `skills/`; no pre-existing source-code modifications were reported before generation.
- Remote URL: https://github.com/clearml/clearml

## Evidence Paths

- `setup.py`
- `setup.cfg`
- `requirements.txt`
- `clearml/version.py`
- `clearml/__init__.py`
- `clearml/task.py`
- `clearml/logger.py`
- `clearml/model.py`
- `clearml/datasets/dataset.py`
- `clearml/storage/manager.py`
- `clearml/storage/helper.py`
- `clearml/automation/`
- `clearml/cli/`
- `clearml/router/`
- `clearml/hyperdatasets/`
- `docs/`
- `examples/`
- `README.md`

## Extraction Notes

- The skill was generated from the base ClearML package scope, with optional extras documented rather than installed broadly.
- `s3`, `gs`, `azure`, and `router` extras are included as workflow-specific install guidance.
- Examples that require ClearML credentials, server access, remote queues, cloud credentials, optional ML frameworks, external datasets, GPU resources, or long training were used as evidence and not executed as runtime checks.
- No generated runtime file should depend on the original repository checkout remaining available.
