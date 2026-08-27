# Aim package overview

Read this reference when deciding how Aim concepts fit together before choosing a sub-skill.

## What Aim does

Aim is an experiment tracking package for AI/ML workflows. It gives user code a Python SDK for recording runs, metrics, parameters, media objects, logs, and artifacts; a local repository format for storing them; query APIs for analyzing tracked data; and CLI/UI/server tools for browsing or tracking remotely.

## Core object model

- **Aim repository**: the storage location for experiment data. CLI commands normally create a `.aim` directory under a user-selected repo root. SDK automation should pass explicit paths rather than relying on the process current directory.
- **Run**: one tracked experiment. A run has a hash, properties such as name/description/experiment/tags, structured run parameters, and typed sequences.
- **Run params**: dictionary-like metadata set with `run[...]`, `run['hparams'] = {...}`, or `run.set(...)`. Query-friendly params should use strings, numbers, booleans, and shallow nested dictionaries.
- **Sequence**: an ordered stream of tracked values for one run, sequence name, and context. Numeric values become metrics; wrapped Aim objects become image/text/audio/distribution/figure sequences.
- **Context**: a dictionary-like discriminator for streams with the same name. Use contexts such as `{"subset": "train"}` and `{"subset": "val"}` rather than creating ambiguous names.
- **Query expressions**: restricted Python expressions over `run` and a sequence variable such as `metric`, `images`, `texts`, or `distributions`.

## Skill routing

- Use `sub-skills/tracking-sdk/SKILL.md` for Python code instrumentation, local run/repo APIs, metrics/media/artifact tracking, exact sequence retrieval, query expressions, and SDK-level missing-data debugging.
- Use `sub-skills/cli-and-services/SKILL.md` for `aim` and `aim-watcher` commands, local UI, remote tracking server, notebook UI, storage/run maintenance, and service/notifier troubleshooting.
- Use `sub-skills/framework-integrations/SKILL.md` for framework callbacks/loggers, optional adapter dependency boundaries, direct `Run.track` fallbacks, and TensorBoard conversion/sync.

## Common end-to-end flow

1. Initialize or select an Aim repository.
   - CLI/user workflow: `aim init --repo <repo-dir>`.
   - SDK automation: `Repo.from_path(str(repo_dir), init=True)`.
2. Instrument code with `Run(repo=repo, experiment=...)`.
3. Track parameters and sequences with explicit `step`, `epoch`, and `context` where possible.
4. Close run and repo resources explicitly in scripts.
5. Inspect locally through SDK queries or start UI/server tools only when the user asked for a listener.
6. For framework-specific code, choose a native callback only when its optional dependency is installed and the callback gives value over direct SDK logging.

## Public prerequisites

- Python package name: `aim`.
- Public imports normally come from `aim`: `Repo`, `Run`, `Image`, `Text`, `Distribution`, `Audio`, and `Figure`.
- CLI entry points: `aim` and `aim-watcher`.
- Base Aim does not require a GPU. User training code may use any backend, but Aim tracking itself can be validated on CPU.
- Optional integrations require their own frameworks, such as Lightning, Transformers, TensorFlow/Keras, XGBoost, LightGBM, CatBoost, Optuna, TensorBoard, or plotting/dataframe libraries.

## Safety boundaries

- Do not run `aim up`, `aim server`, or `aim-watcher start` unless the user wants a long-running listener and has specified process/host/port expectations.
- Do not run destructive commands such as `aim runs rm`, `aim storage restore`, `aim storage prune`, or `aim storage reindex` without listing, backup/restore context, and confirmation.
- Do not install broad optional ML framework stacks unless the user explicitly needs a native adapter or training example.
- Do not use original repository examples, tests, or docs as runtime dependencies. Use the bundled sub-skill scripts and references instead.
