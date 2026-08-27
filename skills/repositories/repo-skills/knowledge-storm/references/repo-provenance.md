# Repository provenance

`schema: disco.repo-provenance.v1`

This skill was distilled from the public STORM / `knowledge-storm` repository and is intended to operate against the public package API rather than the local source checkout.

## Source revision

| Field | Value |
| --- | --- |
| Public repository URL | `https://github.com/stanford-oval/storm` |
| Source commit | `fb951af7744dab086e34962e9bc6fe878e145f83` |
| Branch at extraction | `main` |
| Exact tag | none observed |
| Source status before generated skill outputs | clean |
| Source status after generation | generated `skills/` artifacts make the working tree dirty |
| Package metadata version | `1.1.1` from `setup.py` |
| Imported package version | `knowledge_storm.__version__ == 1.1.0` during inspection |
| Python support evidence | package metadata `>=3.10`; repository CI evidence used Python 3.11 |

## Evidence paths used

Relative source evidence inspected for this skill:

- `README.md`
- `setup.py`
- `requirements.txt`
- `CONTRIBUTING.md`
- `.github/workflows/format-check.yml`
- `.github/workflows/python-package.yml`
- `knowledge_storm/__init__.py`
- `knowledge_storm/lm.py`
- `knowledge_storm/rm.py`
- `knowledge_storm/utils.py`
- `knowledge_storm/encoder.py`
- `knowledge_storm/interface.py`
- `knowledge_storm/dataclass.py`
- `knowledge_storm/logging_wrapper.py`
- `knowledge_storm/storm_wiki/engine.py`
- `knowledge_storm/storm_wiki/modules/knowledge_curation.py`
- `knowledge_storm/storm_wiki/modules/outline_generation.py`
- `knowledge_storm/storm_wiki/modules/article_generation.py`
- `knowledge_storm/storm_wiki/modules/article_polish.py`
- `knowledge_storm/storm_wiki/modules/callback.py`
- `knowledge_storm/storm_wiki/modules/storm_dataclass.py`
- `knowledge_storm/collaborative_storm/engine.py`
- `knowledge_storm/collaborative_storm/modules/callback.py`
- `knowledge_storm/collaborative_storm/modules/co_storm_agents.py`
- `knowledge_storm/collaborative_storm/modules/expert_generation.py`
- `knowledge_storm/collaborative_storm/modules/warmstart_hierarchical_chat.py`
- `examples/storm_examples/README.md`
- `examples/storm_examples/run_storm_wiki_gpt.py`
- `examples/storm_examples/run_storm_wiki_gpt_with_VectorRM.py`
- `examples/storm_examples/helper/process_kaggle_arxiv_abstract_dataset.py`
- `examples/costorm_examples/run_costorm_gpt.py`
- `frontend/demo_light/README.md`
- `frontend/demo_light/storm.py`
- `frontend/demo_light/demo_util.py`
- `frontend/demo_light/pages_util/CreateNewArticle.py`
- `frontend/demo_light/pages_util/MyArticles.py`

## Runtime verification evidence

The private inspection environment verified these facts during construction:

- editable package import succeeded;
- `python -m pip check` reported no broken requirements;
- distribution metadata and live import both worked;
- selected native example `--help` commands rendered successfully for STORM Wiki, VectorRM, Co-STORM, and CSV preprocessing;
- CUDA was visible and torch could allocate a tensor on an NVIDIA A100, but CUDA is optional for this skill's selected workflows.

The private environment path and local checkout path are intentionally not embedded in public runtime instructions. Recreate a normal Python 3.10+ package environment for future use.

## Known limits and staleness triggers

- Full STORM/Co-STORM runs were not executed without credentials; runtime helpers expose dry-run and validation paths to check configuration before expensive calls.
- The full Streamlit demo-light application was treated as reference-only and is not bundled; use `sub-skills/storm-wiki/references/demo-light.md` for distilled setup guidance.
- The source had no dedicated test directory in this checkout, so native verification candidates are example-script/help and synthetic data-validation cases.
- Re-check this skill if `knowledge-storm` changes major APIs, retriever constructor names, `VectorRM`/Qdrant behavior, Co-STORM `RunnerArgument` fields, output-file contracts, or the package version mismatch is resolved.
