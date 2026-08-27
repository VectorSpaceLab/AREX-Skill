# Optuna Package Overview

## When to Read

Read this for a quick map of Optuna's public surfaces, optional dependencies, and which sub-skill owns each workflow.

## Core Public Surfaces

- Study lifecycle: `optuna.create_study`, `optuna.load_study`, `optuna.delete_study`, `optuna.copy_study`, `optuna.study.Study`.
- Trial APIs: `Trial.suggest_float`, `suggest_int`, `suggest_categorical`, `report`, `should_prune`, and `FrozenTrial` result objects.
- Search algorithms: `optuna.samplers` for TPE, random, grid, CMA-ES, QMC, NSGA-II/III, GP, brute force, partial fixed, and custom samplers.
- Early stopping: `optuna.pruners` for median, percentile, successive halving, Hyperband, threshold, patient, Wilcoxon, and custom pruners.
- Persistence and operations: `optuna.storages`, the `optuna` console script, `RDBStorage`, `JournalStorage`, and gRPC proxy storage.
- Analysis: `optuna.importance`, `Study.trials_dataframe`, `optuna.visualization`, and `optuna.visualization.matplotlib`.
- Files and external tools: `optuna.artifacts` and `optuna.integration` lazy imports for framework-specific callbacks.
- Advanced support: `optuna.terminator`, `optuna.search_space`, logging, exceptions, and experimental-warning behavior.

## Dependency Boundaries

Base installation covers core optimization, RDB storage dependencies, YAML-backed CLI behavior, and local artifact APIs. Optional dependencies should be installed only for the workflow that needs them:

| Need | Typical package(s) | Owning route |
| --- | --- | --- |
| Plotly visualizations | `plotly` | `analysis-visualization` |
| Matplotlib visualizations | `matplotlib` | `analysis-visualization` |
| Trial dataframe export | `pandas` | `analysis-visualization` |
| Default fANOVA importances | `scikit-learn` | `analysis-visualization` |
| CMA-ES sampler | `cmaes` | `samplers-pruners` |
| Wilcoxon/QMC/GP-related algorithms | `scipy`, `torch`, `greenlet` depending on feature | `samplers-pruners` |
| Cloud artifact stores | `boto3`, `google-cloud-storage` | `artifacts-integrations` |
| Redis journal backend | `redis` | `cli-and-storage` |
| gRPC storage proxy | `grpcio`, `protobuf` | `cli-and-storage` |
| ML framework callbacks | framework packages plus `optuna-integration` where applicable | `artifacts-integrations` |

## Routing Principle

Start from the user task, not the source module name. For example, a request to tune a sampler belongs in `samplers-pruners`, but a request to run the study using that sampler still needs `optimization-workflows`; a request to resume that study from SQLite also needs `cli-and-storage`.
