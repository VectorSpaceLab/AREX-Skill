# Repo Provenance

- Schema: `disco.repo-provenance.v1`

## Source baseline

- Upstream project: ClovaAI/NAVER Donut, `https://github.com/clovaai/donut`
- Package distribution: `donut-python`
- Import package: `donut`
- Package version in source: `1.0.9`
- Source commit: `4cfcf972560e1a0f26eb3e294c8fc88a0d336626`
- Source branch at construction: `master`
- License: MIT
- Construction state: source files were clean before skill generation; the generated `skills/` tree is construction output and was untracked in the checkout.

## Evidence paths used

Relative source evidence inspected for this skill:

- `README.md`
- `setup.py`
- `donut/__init__.py`
- `donut/_version.py`
- `donut/model.py`
- `donut/util.py`
- `app.py`
- `train.py`
- `test.py`
- `lightning_module.py`
- `config/train_cord.yaml`
- `config/train_docvqa.yaml`
- `config/train_rvlcdip.yaml`
- `config/train_zhtrainticket.yaml`
- `synthdog/README.md`
- `synthdog/template.py`
- `synthdog/elements/background.py`
- `synthdog/elements/content.py`
- `synthdog/elements/document.py`
- `synthdog/elements/paper.py`
- `synthdog/elements/textbox.py`
- `synthdog/layouts/grid.py`
- `synthdog/layouts/grid_stack.py`
- `synthdog/config_en.yaml`
- `synthdog/config_ja.yaml`
- `synthdog/config_ko.yaml`
- `synthdog/config_zh.yaml`

## Included and excluded extraction scope

Included in the operating graph:

- public package APIs in `donut/`;
- inference/demo behavior from `app.py`, `README.md`, and `donut/model.py`;
- training/evaluation behavior from `train.py`, `test.py`, `lightning_module.py`, and `config/`;
- SynthDoG template/config/resource-layout behavior from `synthdog/`;
- installation, dependency, backend, and data-format guidance from package metadata and docs.

Excluded from runtime skill content:

- `.git/`, build/cache files, and repository metadata;
- large datasets and model outputs under `dataset/` or `result/` if present;
- large SynthDoG resource assets, which are documented as external inputs rather than bundled;
- construction review reports and verification artifacts under `skills/tests/`.

## Runtime inspection baseline

During construction, a private inspection environment verified these public facts without embedding any private paths into the skill:

- `donut` import succeeded from a neutral working directory;
- package version was `donut-python==1.0.9` from the source checkout;
- core signatures were captured for `DonutConfig`, `DonutModel`, `DonutDataset`, `JSONParseEvaluator`, `DonutModel.inference`, and `DonutModel.from_pretrained`;
- `app.py --help`, `train.py --help`, `test.py --help`, and `synthtiger --help` succeeded;
- `pip check` passed with a modern compatible stack including PyTorch 2.5.1+CUDA 12.4, Transformers 4.38.2, Gradio 4.44.1, SynthTIGER 1.2.1, NumPy 1.26.4, and OpenCV 4.11.0;
- CUDA was available on the construction host and was treated as required for training coverage.

These versions are evidence, not a promise that every user environment must match exactly. Use the troubleshooting reference and root smoke script to validate a target runtime.

## Refresh triggers

Refresh this skill when any of the following change:

- package version, public exports, or public API signatures;
- `from_pretrained` revision behavior or Hugging Face model-loading assumptions;
- inference output structure or prompt/token conversion behavior;
- dataset JSONL contract or evaluator metrics;
- training CLI/config/Lightning behavior;
- SynthDoG template, config placeholders, resource layout, or dependencies;
- dependency compatibility for PyTorch, Transformers, Gradio, datasets, pytorch-lightning, or SynthTIGER.
