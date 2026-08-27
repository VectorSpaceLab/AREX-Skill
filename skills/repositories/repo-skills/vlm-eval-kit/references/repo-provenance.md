# VLMEvalKit repo provenance

## Source snapshot

- Public project name: VLMEvalKit
- Python distribution name: `vlmeval`
- Python import root: `vlmeval`
- Console entry point from package metadata: `vlmutil = vlmeval:cli`
- Main evaluation entry in repository distributions: `run.py`
- Source commit: `fd09032341aed9f1e85b761745154299e13f50c0`
- Source branch: `main`
- Exact tag: none detected
- Public remote URL: `https://github.com/open-compass/VLMEvalKit.git`
- Working tree state at generation: dirty because the generated `skills/` output tree was untracked; no source-code changes outside generated skill/review artifacts were observed.
- Package metadata version from `setup.py` / installed distribution: `0.1.0`
- Source `vlmeval.__version__`: `0.2rc1`

## Evidence paths used

- `README.md`
- `docs/en/Quickstart.md`
- `docs/en/ConfigSystem.md`
- `docs/en/Development.md`
- `docs/en/EvalByLMDeploy.md`
- `setup.py`, `setup.cfg`, `requirements.txt`, `requirements/docs.txt`
- `run.py`
- `vlmeval/__init__.py`
- `vlmeval/config.py`
- `vlmeval/tools.py`
- `vlmeval/inference.py`, `vlmeval/inference_mt.py`, `vlmeval/inference_video.py`, `vlmeval/inference_api.py`
- `vlmeval/api/base.py`, `vlmeval/api/litellm_api.py`, `vlmeval/api/lmdeploy.py`, `vlmeval/api/openai_sdk.py`, `vlmeval/api/__init__.py`
- `vlmeval/api/adapters/base.py`, `vlmeval/api/adapters/internvl2.py`, `vlmeval/api/adapters/internvl3.py`, `vlmeval/api/adapters/interns1_1.py`
- `vlmeval/vlm/base.py`, `vlmeval/vlm/__init__.py`
- `vlmeval/dataset/__init__.py`, `vlmeval/dataset/image_base.py`, `vlmeval/dataset/text_base.py`, `vlmeval/dataset/video_base.py`, `vlmeval/dataset/image_mcq.py`, `vlmeval/dataset/video_dataset_config.py`
- `vlmeval/dataset/utils/judge_util.py`, `vlmeval/dataset/utils/multiple_choice.py`
- `vlmeval/smp/file.py`, `vlmeval/smp/status_report.py`, `vlmeval/smp/misc.py`, `vlmeval/smp/vlm.py`
- `tests/test_litellm_api.py`, `tests/test_inference_api.py`
- `scripts/run.sh`, `scripts/apires_scan.py`, `scripts/summarize.py`, `scripts/build_longdocurl_tsv.py`, plus related converter scripts classified in the source-script map.

## Verification baseline

- Python package import and selected API signatures were inspected from a private prepared environment.
- Native lightweight tests passed:
  - `tests/test_litellm_api.py`: 22 passed.
  - `tests/test_inference_api.py`: 5 passed, with NumPy reload warnings caused by repeated module loading in the test.
- CLI/help checks passed for `run.py --help`, `vlmutil dlist l1`, and `vlmutil mlist all`.
- A torch CUDA smoke check found visible NVIDIA GPU devices and allocated a tiny CUDA tensor, but large model runs were not executed.
- Live API calls, dataset downloads, Gradio services, and full benchmark evaluations were intentionally not executed during skill creation.

## Refresh triggers

Refresh this skill when any of these change materially:

- `run.py` flags, `--api-mode`, result layout, reuse/status semantics, or `PRED_FORMAT`/`SPLIT_THINK` handling.
- `BaseModel`, `BaseAPI`, `LiteLLMAPI`, `LMDeployAPI`, prompt-adapter hooks, or `supported_VLM` registration patterns.
- Dataset base class contracts, `build_dataset`, `supported_video_datasets`, TSV/video schemas, or MCQ/judge evaluation helpers.
- Requirements or Python/Torch/Transformers compatibility recommendations.
- Source scripts used as bundled helpers or reference-only converter patterns.
