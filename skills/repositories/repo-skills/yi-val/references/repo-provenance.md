# Repo provenance

Schema: `disco.repo-provenance.v1`

## Source baseline

- Project branding: **YiVal**
- Python distribution/package: `yival`
- Source repository: `https://github.com/YiVal/YiVal.git`
- Baseline commit used for this skill: `22a1fa0e3ed27b8e2639a8340d6c3662e64c4e2f`
- Baseline branch observed: `master`
- Exact tag at baseline: none observed
- Declared package version: `0.0.0` in `pyproject.toml` with dynamic VCS versioning enabled
- Generated skill id: `yi-val`

## Evidence used

The skill distills the public package surface and repo-owned documentation from:

- Package metadata: `pyproject.toml`, `poetry.lock`, `README.md`, `CHANGELOG.md`, `LICENSE`.
- Public CLI and runtime modules: `src/yival/__main__.py`, `src/yival/cli/`, `src/yival/experiment/`.
- Config/data/generator/evaluator/selector/enhancer/wrapper schemas and implementations under `src/yival/`.
- Packaged demo functions, configs, and data under `src/yival/demo/`.
- Documentation: architecture, interactive mode, QA expected results, auto prompt generation, and custom-class guides.
- Native tests for CLI helpers, config loading, readers, data processor, wrappers, experiment state, evaluators, AHP selection, logger, output parsers, and variation-generator registry behavior.

## Environment facts at creation

- A Python 3.11 inspection environment successfully installed the package in editable mode with test dependencies.
- `pip check` passed after installation.
- `yival --help` and `yival init --help` imported successfully after using a setuptools version that still exposes `pkg_resources`.
- Built-in registries are populated only after the corresponding implementation modules are imported.
- The host had CUDA-capable hardware, but no required accelerator backend is needed for the selected core skill scope.

## Scope decisions

Included in this operating graph:

- CLI/config creation, validation, and routing.
- YAML experiment structure and data sources.
- `ExperimentRunner`, `LiteExperimentRunner`, `ExperimentState`, `StringWrapper`, and result artifacts.
- CSV and Hugging Face dataset readers.
- OpenAI prompt data generator, document data generator, OpenAI prompt variation generator, chain-of-density prompt generator, and self-exemplar generator.
- String expected result, Python validation, BERTScore, ROUGE, OpenAI prompt-based, OpenAI Elo, and AlpacaEval evaluators.
- AHP selection and prompt enhancers.
- Custom component extension contracts.

Excluded or treated as limited:

- Local SFT and external fine-tuning helpers in `src/yival/finetune/` are optional, costly, and dependency-heavy; they require explicit user approval before use.
- Demo scripts that call OpenAI, Replicate, Midjourney, Guardrails, external datasets, FAISS embeddings, or arbitrary code execution are reference evidence, not bundled runtime commands.
- Website, Docker, CI, generated outputs, and production logs are not part of the runtime operating graph.

## Refresh guidance

Refresh this skill when source changes alter:

- CLI subcommands or flags.
- `ExperimentConfig`, `DatasetConfig`, evaluator/selector/enhancer config dataclasses, or YAML field names.
- Registry ids for readers, wrappers, data generators, variation generators, evaluators, selectors, or enhancers.
- OpenAI SDK compatibility, especially if YiVal migrates from `openai.ChatCompletion` to a newer client API.
- Optional trainer extras or fine-tuning support.
- UI launch behavior for Dash, Streamlit, or ngrok.
