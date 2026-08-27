# Repo provenance

- Schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository: CVAT (Computer Vision Annotation Tool)
- Public remote: `https://github.com/cvat-ai/cvat.git`
- Commit: `7a541caa853e859f913aeff618b15fff226b726a`
- Branch: `develop`
- Exact tag: none detected at this commit
- Dirty state at construction: generated `skills/` output was untracked; no source-file modifications were required for public skill content.
- License: MIT for core repository code; serverless assets and dependencies may have separate licenses.

## Version evidence

- CVAT core metadata: `2.72.1-alpha.0` from `cvat/__init__.py`.
- `cvat-cli` package metadata: `2.72.1` from `cvat-cli/pyproject.toml` and `cvat-cli/src/cvat_cli/version.py`.
- `cvat-sdk` package metadata: dynamic `2.72.1` from `cvat-sdk/pyproject.toml` / SDK version module generation convention.
- Frontend package examples: `cvat-ui` `2.72.1`, `cvat-core` `15.3.1`, `cvat-data` `2.1.0`, `cvat-canvas` `2.20.10`, `cvat-canvas3d` `0.0.10`.

## Evidence paths used

- `README.md`
- `cvat-sdk/README.md`
- `cvat-sdk/pyproject.toml`
- `cvat-sdk/cvat_sdk/core/client.py`
- `cvat-sdk/cvat_sdk/core/auth.py`
- `cvat-sdk/cvat_sdk/core/proxies/tasks.py`
- `cvat-sdk/cvat_sdk/core/proxies/projects.py`
- `cvat-sdk/cvat_sdk/auto_annotation/interface.py`
- `cvat-sdk/cvat_sdk/auto_annotation/driver.py`
- `cvat-sdk/cvat_sdk/datasets/`
- `cvat-sdk/cvat_sdk/pytorch/`
- `cvat-cli/README.md`
- `cvat-cli/pyproject.toml`
- `cvat-cli/src/cvat_cli/__main__.py`
- `cvat-cli/src/cvat_cli/_internal/commands_tasks.py`
- `cvat-cli/src/cvat_cli/_internal/commands_projects.py`
- `cvat-cli/src/cvat_cli/_internal/commands_functions.py`
- `cvat-cli/src/cvat_cli/_internal/common.py`
- `site/content/en/docs/api_sdk/`
- `site/content/en/docs/dataset_management/`
- `site/content/en/docs/annotation/auto-annotation/`
- `site/content/en/docs/administration/community/`
- `site/content/en/docs/contributing/development-environment.md`
- `site/content/en/docs/contributing/running-tests.md`
- `components/serverless/docker-compose.serverless.yml`
- `components/serverless/README.md`
- `serverless/deploy_cpu.sh`
- `serverless/deploy_gpu.sh`
- `utils/dataset_manifest/create.py`
- `utils/dicom_converter/README.md`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `helm-chart/README.md`

## Refresh guidance

Refresh this skill when CVAT changes SDK/CLI command names, auth/profile resolution, API object signatures, dataset format names, serverless deployment scripts, compose overlays, package extras, or version compatibility rules. Also refresh after major CVAT releases if server and SDK minor-version compatibility behavior changes.
