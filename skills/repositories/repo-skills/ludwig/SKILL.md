---
name: ludwig
description: "Guides agents using Ludwig declarative machine learning configs,
  CLI commands, Python APIs, AutoML, HPO, serving, export, and deployment
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Ludwig Repo Skill

Use this skill when the task is about Ludwig, a declarative machine-learning framework that trains, fine-tunes, evaluates, serves, exports, and inspects models from YAML configs or the `LudwigModel` Python API.

## First checks

1. Confirm the task is using Ludwig as an installed package or intends to create Ludwig YAML/config/API calls. If the task is about editing this repository itself, use the maintainer notes in the relevant sub-skill and keep changes source-backed.
2. Confirm Python 3.12+ for current Ludwig releases.
3. Start with a minimal import check before relying on optional workflows:

```bash
python -c "import ludwig; print(ludwig.__version__)"
ludwig --help
```

4. For a structured environment check, run the bundled helper:

```bash
python scripts/check_env.py --check-cli
```

Read [installation-and-extras.md](references/installation-and-extras.md) for extras and backend decisions. Read [troubleshooting.md](references/troubleshooting.md) when imports, optional dependencies, configs, data columns, GPU paths, servers, or artifact paths fail.

## Route by task

| User intent | Read this |
| --- | --- |
| Write or validate a Ludwig YAML config, generate a config from natural language, initialize/render a config, export JSON schema, prepare CSV/JSON/Parquet data, synthesize a tiny dataset, or debug config/data validation | [configuration-and-data](sub-skills/configuration-and-data/SKILL.md) |
| Run `ludwig train`, `ludwig experiment`, `ludwig check_install`, or Python `LudwigModel.train/experiment`; plan ECD, LLM, VLM, multimodal, timeseries, adapter, or quantization training | [training-and-experiments](sub-skills/training-and-experiments/SKILL.md) |
| Load a trained model, predict, evaluate, forecast, inspect, collect weights/activations, reason about prediction/evaluation outputs, or use `LudwigModel.predict/evaluate/forecast/generate` | [prediction-evaluation-and-inspection](sub-skills/prediction-evaluation-and-inspection/SKILL.md) |
| Use AutoML, `init_config`, `auto_train`, `hyperopt`, Ray/Optuna executors, search spaces, or distributed tuning | [automl-and-hyperopt](sub-skills/automl-and-hyperopt/SKILL.md) |
| Serve a model, build `/predict` or `/batch_predict` payloads, use FastAPI/Ray Serve/KServe/vLLM shims, export models, export MLflow, or upload to a hub | [serving-export-and-deployment](sub-skills/serving-export-and-deployment/SKILL.md) |
| Need all CLI subcommands and common flags | [cli-reference.md](references/cli-reference.md) |
| Need stable Python API signatures and return shapes | [api-reference.md](references/api-reference.md) |
| Need to know whether this skill matches a current checkout | [repo-provenance.md](references/repo-provenance.md) |

## Core Ludwig mental model

- Ludwig configs declare `input_features`, `output_features`, optional `combiner`, `trainer`, `backend`, preprocessing, hyperopt, adapter, quantization, and model-type sections.
- Use `model_type: ecd` for ordinary encoder-combiner-decoder models over tabular, text, image, audio, timeseries, vector, H3, and related features. Use `model_type: llm` for LLM fine-tuning/generation workflows.
- CLI commands and Python APIs share the same config concepts. Prefer the CLI for reproducible shell workflows and `LudwigModel` when embedding training/prediction in Python.
- Output artifacts usually live under an output directory with experiment/model run subdirectories, model weights/config metadata, training statistics, prediction files, and optional logs/reports.
- GPU, Ray, KServe, vLLM, provider APIs, Hub uploads, and external dataset downloads are optional operational paths. Verify prerequisites before claiming they work.

## Safe workflow defaults

- Use tiny local fixtures first. The bundled data/training helpers create local CSV/config files without network or credentials.
- Prefer help/schema/import checks before long training or server startup.
- Never start a long-running server, download large datasets/models, launch Ray clusters, upload artifacts, or run GPU LLM fine-tuning unless the user explicitly asks and the environment is prepared.
- When a workflow mentions optional extras, diagnose the missing package and suggest the narrow extra rather than installing `full` by default.

## Evidence and staleness

This skill was distilled from source, package metadata, examples, and focused tests listed in [repo-provenance.md](references/repo-provenance.md). If the package version, CLI commands, config schema, or source commit differs, refresh this skill before relying on exact signatures or option names.
