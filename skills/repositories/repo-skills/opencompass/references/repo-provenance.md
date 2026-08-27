# Repo Provenance

## Source Baseline

- Project: OpenCompass
- Skill id: `opencompass`
- Package/distribution: `opencompass`
- Package version: `0.5.2`
- Source commit: `8b14385f925aa19310404c72001b15a20ec6d184`
- Source branch: `main`
- Exact tag: none detected
- Remote URL: `https://github.com/open-compass/opencompass.git`
- Working tree state at generation: dirty because this generated `skills/` tree was added during skill creation; no pre-existing source changes were detected before generation.

## Evidence Paths

- `setup.py`
- `requirements/runtime.txt`
- `requirements/api.txt`
- `requirements/lmdeploy.txt`
- `requirements/vllm.txt`
- `requirements/extra.txt`
- `README.md`
- `docs/en/get_started/installation.md`
- `docs/en/get_started/quick_start.md`
- `docs/en/get_started/faq.md`
- `docs/en/user_guides/config.md`
- `docs/en/user_guides/datasets.md`
- `docs/en/user_guides/evaluation.md`
- `docs/en/user_guides/models.md`
- `docs/en/user_guides/summarizer.md`
- `docs/en/prompt/prompt_template.md`
- `docs/en/prompt/meta_template.md`
- `docs/en/advanced_guides/new_dataset.md`
- `docs/en/advanced_guides/new_model.md`
- `docs/en/advanced_guides/accelerator_intro.md`
- `docs/en/advanced_guides/llm_judge.md`
- `opencompass/cli/main.py`
- `opencompass/configs/`
- `opencompass/datasets/`
- `opencompass/evaluator/`
- `opencompass/metrics/`
- `opencompass/models/`
- `opencompass/openicl/`
- `opencompass/partitioners/`
- `opencompass/runners/`
- `opencompass/summarizers/`
- `opencompass/tasks/`
- `tools/`
- `tests/`

## Verified Package Facts

- `opencompass` imports and reports version `0.5.2`.
- Distribution metadata for `opencompass` reports version `0.5.2`.
- Console entry point metadata includes `opencompass = opencompass.cli.main:main`.
- `opencompass --help` exposes model/dataset/summarizer selectors, config positional argument, `--debug`, `--dry-run`, `--accelerator`, `--mode`, `--reuse`, `--work-dir`, runner options, HF model options, and custom dataset options.
- `PromptTemplate`, `ZeroRetriever`, and OpenCompass registries for models, dataset loading, evaluators, retrievers, and inferencers import in the inspection environment.

## Refresh Notes

Refresh this skill when OpenCompass changes CLI flags, config layout, package extras, runner/partitioner APIs, model backend names, prompt/inferencer behavior, summarizer output schema, or LLM-judge configuration patterns.
