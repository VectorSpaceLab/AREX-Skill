# PaddleX repo provenance

## Source version

- Repository: PaddleX
- Canonical skill id: `paddlex`
- Source commit inspected: `ffb64904d23708863ff5b8da312a5cbd52a7f462`
- Branch inspected: `release/3.7`
- Tag observed: `v3.7.2`
- Package version verified from installed metadata: `paddlex 3.7.2`
- Source-analysis dirty state: no dirty source files were observed before skill generation. This runtime skill is a generated construction output.

## Installed-package facts verified during construction

- `import paddlex` succeeded.
- `paddlex.__version__ == "3.7.2"`.
- CPU `paddlepaddle==3.3.0` executed a small tensor operation.
- `paddlex --help` and `python -m paddlex --help` exposed install, pipeline predict, serving, and Paddle2ONNX option groups.
- Console entry points included `paddlex` and `paddlex_genai_server`.

## Evidence paths used

- `README.md`, `README_en.md`
- `setup.py`, `pyproject.toml`
- `main.py`, `install_pdx.py`
- `paddlex/__init__.py`, `paddlex/__main__.py`, `paddlex/paddlex_cli.py`
- `paddlex/model.py`, `paddlex/engine.py`, `paddlex/modules/`
- `paddlex/inference/`, including pipeline, serving, HPI, and GenAI code paths
- `paddlex/configs/pipelines/*.yaml`
- `paddlex/configs/modules/**/*.yaml`
- `paddlex/utils/config.py`, `paddlex/utils/deps.py`, `paddlex/utils/pipeline_arguments.py`
- `paddlex/repo_manager/`
- `docs/installation/`
- `docs/pipeline_usage/`
- `docs/module_usage/`
- `docs/pipeline_deploy/`
- `docs/support_list/`
- `docs/other_devices_support/`
- `docs/practical_tutorials/`
- `docs/data_annotations/`
- `api_examples/pipelines/*.py`
- `tools/check_docs_github_links.py`, `tools/resolve_doc_github_refs.py` as maintainer-only exclusion evidence
- `tests/` as CI/native-candidate exclusion evidence
- `skills/PaddleX.log` as prior run evidence only

## Staleness checks for future refresh

Refresh this skill if any of these change materially:

- PaddleX major/minor version, especially public API signatures or CLI options.
- pipeline names, config schema, or result save methods.
- module config modes, dataset checker/trainer/evaluator APIs, or supported model families.
- deployment plugin names, HPI backend selection, Paddle2ONNX plugin version, serving command behavior, or GenAI backend support.
- PaddlePaddle version requirements or hardware/backend compatibility notes.
