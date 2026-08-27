# Optuna Cross-Cutting Troubleshooting

## Install or Import Fails

Symptoms: `ModuleNotFoundError: optuna`, missing base dependencies such as `colorlog`, or an installed package that imports from the wrong environment.

Fix:

```bash
python -m pip install optuna
python -m pip check
python - <<'PY'
import optuna
print(optuna.__version__)
PY
```

For a source checkout, use `python -m pip install -e .` only when local development is intended. Do not rely on running Python from a checkout without installing dependencies.

## Optional Dependency Missing

Symptoms include errors naming `plotly`, `matplotlib`, `pandas`, `sklearn`, `cmaes`, `scipy`, `torch`, `boto3`, `google.cloud`, `redis`, `grpc`, or a framework integration package.

Fix by routing to the owning sub-skill and installing only the needed optional package. Missing optional packages do not usually break core `create_study` or `Study.optimize` workflows.

## CLI Cannot Find Storage

Symptoms: CLI commands create empty studies unexpectedly, cannot find study names, or fail unless `--storage` is repeated.

Fix:

```bash
export OPTUNA_STORAGE=sqlite:///example.db
optuna create-study --study-name demo --direction minimize
optuna ask --study-name demo --search-space '{"x": {"name": "FloatDistribution", "attributes": {"low": 0.0, "high": 1.0, "log": false, "step": null}}}' --format json
```

Use `sub-skills/cli-and-storage/references/cli-reference.md` for exact command sequences.

## Study Direction or Value Mismatch

Symptoms: `Study.tell` fails or warns because a single value was supplied to a multi-objective study, or an objective returns the wrong number of values.

Fix: align `direction=` with one scalar objective, or `directions=[...]` with one returned value per direction. Use `sub-skills/optimization-workflows/references/troubleshooting.md` for lifecycle details.

## Pruning Has No Effect

Symptoms: a pruner is configured but no trial is pruned.

Fix: inside the objective, call `trial.report(value, step)` at meaningful steps and raise `optuna.TrialPruned()` when `trial.should_prune()` returns true. Also check warmup/startup settings in `samplers-pruners`.

## Cloud, Distributed, or Integration Workflows Need Credentials

Do not run network or credentialed checks by default. For S3/GCS, Redis, gRPC, MLflow, W&B, or framework integrations, first verify the optional SDK and credentials, then use local filesystem or SQLite smoke tests when credentials are absent.
