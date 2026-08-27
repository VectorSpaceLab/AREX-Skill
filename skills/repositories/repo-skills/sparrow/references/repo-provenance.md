# Repo provenance

Schema: `disco.repo-provenance.v1`

## Source snapshot

- Source repository: Sparrow public source checkout (remote URL omitted as private or unknown in this production context)
- Branch: `main`
- Commit: `b53bf5988f916cce6f5ed6cd82d4e46d06fc4f7c`
- Exact tag: none detected
- Working tree state at snapshot time: dirty due generated/untracked `skills/` production artifacts
- License evidence: GPL-3.0 license files present in the repo and selected subcomponents

## Version evidence

- Sparrow platform version: `0.6.0` from root README badge
- `sparrow-parse` distribution/package version: `1.5.6` from package metadata and `sparrow_parse.__version__`
- Next UI package version: `0.1.0` from UI package metadata

## Evidence paths used

- `README.MD`
- `CHANGELOG.md`
- `environment_setup.md`
- `sparrow-data/parse/README.md`
- `sparrow-data/parse/setup.py`
- `sparrow-data/parse/requirements.txt`
- `sparrow-data/parse/sparrow_parse/`
- `sparrow-data/parse/sparrow_parse/test_extraction_*.py`
- `sparrow-data/ocr/README.MD`
- `sparrow-data/ocr/api.py`
- `sparrow-data/ocr/routers/ocr.py`
- `sparrow-data/ocr/requirements.txt`
- `sparrow-ml/llm/api.py`
- `sparrow-ml/llm/engine.py`
- `sparrow-ml/llm/config_utils.py`
- `sparrow-ml/llm/config.properties`
- `sparrow-ml/llm/requirements_sparrow_parse.txt`
- `sparrow-ml/llm/requirements_instructor.txt`
- `sparrow-ml/llm/pipelines/`
- `sparrow-ml/agents/api.py`
- `sparrow-ml/agents/base.py`
- `sparrow-ml/agents/tasks.py`
- `sparrow-ml/agents/celery_config.py`
- `sparrow-ml/agents/config.properties`
- `sparrow-ml/agents/*/agent.py`
- `sparrow-ml/agents/*/sparrow_client.py`
- `sparrow-ml/agents/bonds/*.json`
- `sparrow-ui/README.md`
- `sparrow-ui/shell/README.md`
- `sparrow-ui/shell/*.py`
- `sparrow-ui/shell/requirements.txt`
- `sparrow-ui/shell-next/package.json`
- `sparrow-ui/shell-next/app/`
- `sparrow-ui/shell-next/components/`
- `sparrow-ui/shell-next/lib/`

## Inspection summary

A private Python 3.12 environment was used only as construction evidence. Public runtime guidance in this skill intentionally omits local paths and activation commands. Verified facts retained in public form:

- `sparrow-parse==1.5.6` metadata and import succeeded.
- `python -m sparrow_parse` works as a package self-message.
- The declared `sparrow-parse` console script is broken in this source snapshot.
- Sparrow LLM API routes and `engine.run` options match the bundled API/CLI references.
- Optional backend execution was not treated as verified unless covered by bundled offline smoke scripts.

## Refresh triggers

Refresh this skill when any of these change:

- `sparrow-parse` version, setup metadata, extras, or entry points.
- Sparrow LLM API endpoint names, form fields, option parsing, query preparation, validation, table-template behavior, or config keys.
- OCR endpoint request/response shape, accepted file types, first-page PDF behavior, or PaddleOCR model setup.
- Agent endpoint paths, built-in agent registration, Celery queue behavior, config keys, or domain agent payload schemas.
- UI service topology, upload validation, Next package scripts/dependencies, dashboard database integration, or protected-access behavior.
