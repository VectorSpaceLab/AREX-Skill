#!/usr/bin/env python3
"""Print a compact live signature map for the installed imbalanced-learn APIs."""

from __future__ import annotations

import inspect

from imblearn import show_versions
from imblearn.base import FunctionSampler, is_sampler
from imblearn.combine import SMOTEENN, SMOTETomek
from imblearn.datasets import fetch_datasets, make_imbalance
from imblearn.ensemble import (
    BalancedBaggingClassifier,
    BalancedRandomForestClassifier,
    EasyEnsembleClassifier,
    RUSBoostClassifier,
)
from imblearn.metrics import classification_report_imbalanced, geometric_mean_score
from imblearn.metrics.pairwise import ValueDifferenceMetric
from imblearn.model_selection import InstanceHardnessCV
from imblearn.over_sampling import ADASYN, RandomOverSampler, SMOTE, SMOTENC, SMOTEN
from imblearn.pipeline import Pipeline, make_pipeline
from imblearn.tensorflow import balanced_batch_generator
from imblearn.under_sampling import RandomUnderSampler, TomekLinks
from imblearn.utils import check_neighbors_object, check_sampling_strategy, check_target_type

PUBLIC_OBJECTS = [
    FunctionSampler,
    RandomOverSampler,
    ADASYN,
    SMOTE,
    SMOTENC,
    SMOTEN,
    RandomUnderSampler,
    TomekLinks,
    SMOTEENN,
    SMOTETomek,
    BalancedBaggingClassifier,
    BalancedRandomForestClassifier,
    EasyEnsembleClassifier,
    RUSBoostClassifier,
    InstanceHardnessCV,
    Pipeline,
    make_pipeline,
    make_imbalance,
    fetch_datasets,
    geometric_mean_score,
    classification_report_imbalanced,
    ValueDifferenceMetric,
    balanced_batch_generator,
    is_sampler,
    check_neighbors_object,
    check_sampling_strategy,
    check_target_type,
    show_versions,
]

OPTIONAL_OBJECTS = []
for module_path, import_name in [
    ("imblearn.keras", "BalancedBatchGenerator"),
]:
    try:
        module = __import__(module_path, fromlist=[import_name])
        OPTIONAL_OBJECTS.append(getattr(module, import_name))
    except Exception as exc:  # pragma: no cover - optional backend path
        OPTIONAL_OBJECTS.append(
            f"{module_path}.{import_name} unavailable: {type(exc).__name__}"
        )


def main() -> int:
    for obj in PUBLIC_OBJECTS + OPTIONAL_OBJECTS:
        if isinstance(obj, str):
            print(obj)
            continue
        try:
            sig = inspect.signature(obj)
        except (TypeError, ValueError):
            sig = "<no signature>"
        name = getattr(obj, "__qualname__", getattr(obj, "__name__", repr(obj)))
        module = getattr(obj, "__module__", "")
        print(f"{module}.{name}: {sig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
