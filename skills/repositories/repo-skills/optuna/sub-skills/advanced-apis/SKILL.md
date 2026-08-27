---
name: advanced-apis
description: "Advanced Optuna support APIs for terminator stopping, search-space
  inspection, hypervolume helpers, constraints notes, logging, exceptions,
  experimental warnings, and extension/debugging patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Optuna Advanced APIs

Use this sub-skill when the task is about advanced, user-facing support APIs and cross-cutting debugging around Optuna studies: `optuna.terminator`, `optuna.search_space`, Optuna logging controls, Optuna-specific exceptions, `ExperimentalWarning`, constrained/multi-objective support notes, and internal hypervolume utilities that sometimes appear in advanced multi-objective workflows.

## Route Boundaries

- Stay here for `Terminator`, `TerminatorCallback`, `report_cross_validation_scores`, `IntersectionSearchSpace`, `intersection_search_space`, Optuna logger configuration, `optuna.exceptions`, `ExperimentalWarning`, private `_hypervolume` adaptation notes, and constraint debugging concepts.
- Route core `Study.optimize`, `Study.ask`, `Study.tell`, objective authoring, callbacks in general, and result extraction to `../optimization-workflows/SKILL.md`.
- Route sampler/pruner choice, `constraints_func` constructor tuning, and algorithm-specific behavior to `../samplers-pruners/SKILL.md`.
- Route RDB/CLI/storage operations and heartbeat behavior to `../cli-and-storage/SKILL.md`.
- Route artifact stores and optional third-party integrations to `../artifacts-integrations/SKILL.md`.
- Route plotting, parameter importances, and dashboard-style analysis to `../analysis-visualization/SKILL.md`.

## Fast Paths

- Start with `references/advanced-api-reference.md` for exact APIs, version/stability notes, and copy-paste patterns.
- Use `references/troubleshooting.md` for import failures, optional dependency absence, terminator warnings, empty search spaces, logging duplication, constraints issues, and exception triage.
- Run the bundled smoke check in an environment where `optuna` is importable:
  - `python scripts/terminator_smoke.py`

## Terminator Pattern

`optuna.terminator` is deprecated as of Optuna 4.9.0 and planned for removal in 6.0.0. Use it only for legacy or explicitly requested workflows, and expect `FutureWarning` when constructing terminator objects.

```python
import optuna
from optuna.terminator import BestValueStagnationEvaluator
from optuna.terminator import StaticErrorEvaluator
from optuna.terminator import Terminator
from optuna.terminator import TerminatorCallback

def objective(trial: optuna.Trial) -> float:
    x = trial.suggest_float("x", -1.0, 1.0)
    return x * x


study = optuna.create_study(direction="minimize")
terminator = Terminator(
    improvement_evaluator=BestValueStagnationEvaluator(max_stagnation_trials=5),
    error_evaluator=StaticErrorEvaluator(constant=0.0),
    min_n_trials=3,
)
study.optimize(objective, n_trials=100, callbacks=[TerminatorCallback(terminator)])
```

## Search-Space Pattern

```python
from optuna.search_space import IntersectionSearchSpace

search_space = IntersectionSearchSpace()
study.optimize(objective, n_trials=5)
print(search_space.calculate(study))
```

Intersection search spaces include only parameters whose distributions are present and equal across completed trials. Conditional or changing distributions can shrink the result to `{}`.

## Key Rules

- `Terminator.should_terminate(study)` stops only when the evaluated improvement is strictly smaller than the evaluated error and the number of complete trials is at least `min_n_trials`.
- `report_cross_validation_scores(trial, scores)` requires more than one score and stores scores for `CrossValidationErrorEvaluator`.
- `IntersectionSearchSpace` instances are intended for one study; with persistent storage, reusing one instance across different studies raises `ValueError`.
- `optuna.logging` controls Optuna's library root logger; enable propagation and disable the default handler when integrating with application logging to avoid duplicate stderr output.
- Treat `optuna._hypervolume` as private: useful for advanced diagnostics or adaptation, but not a stable public API contract.
- Use `optuna.exceptions.ExperimentalWarning` or Python warning filters when an experimental API warning is expected and intentional.

## Hard Usability Cases

- Add a safe `TerminatorCallback` to a deterministic objective, explain why `FutureWarning` appears, and verify that the callback stops after a custom `BaseTerminator.should_terminate` condition.
- Debug a conditional search space where `IntersectionSearchSpace.calculate(study)` returns `{}` after trials use the same parameter name with different distributions, while also filtering expected `ExperimentalWarning` noise.
