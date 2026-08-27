#!/usr/bin/env python3
"""Run tiny River supervised-model smoke checks."""

from __future__ import annotations

import argparse
import json
import math
import sys


def _binary_rows():
    return [
        ({"x": -2.0, "bias": 1.0}, False),
        ({"x": -1.0, "bias": 1.0}, False),
        ({"x": 1.0, "bias": 1.0}, True),
        ({"x": 2.0, "bias": 1.0}, True),
    ]


def _regression_rows():
    return [
        ({"x": -2.0, "bias": 1.0}, -3.0),
        ({"x": -1.0, "bias": 1.0}, -1.0),
        ({"x": 0.0, "bias": 1.0}, 1.0),
        ({"x": 1.0, "bias": 1.0}, 3.0),
        ({"x": 2.0, "bias": 1.0}, 5.0),
    ]


def _repeat_learn(model, rows, repeats, weighted=False):
    for _ in range(repeats):
        for i, (x, y) in enumerate(rows):
            if weighted:
                model.learn_one(x, y, w=1.0 + (i % 2))
            else:
                model.learn_one(x, y)
    return model


def check_linear(repeats):
    from river import linear_model, optim

    clf = linear_model.LogisticRegression(
        optimizer=optim.SGD(0.2),
        loss=optim.losses.Log(),
        clip_gradient=10.0,
    )
    _repeat_learn(clf, _binary_rows(), repeats, weighted=True)
    proba = clf.predict_proba_one({"x": 1.5, "bias": 1.0})
    if set(proba) != {False, True} or proba[True] <= proba[False]:
        raise AssertionError(f"unexpected logistic probabilities: {proba!r}")

    reg = linear_model.LinearRegression(
        optimizer=optim.SGD(0.05),
        loss=optim.losses.Huber(epsilon=1.0),
        intercept_lr=0.05,
        clip_gradient=10.0,
    )
    _repeat_learn(reg, _regression_rows(), repeats, weighted=True)
    low = reg.predict_one({"x": -1.5, "bias": 1.0})
    high = reg.predict_one({"x": 1.5, "bias": 1.0})
    if not isinstance(low, float) or not isinstance(high, float) or high <= low:
        raise AssertionError(f"unexpected regression predictions: {low!r}, {high!r}")
    return {"logistic_positive_probability": proba[True], "regression_low": low, "regression_high": high}


def check_tree(repeats):
    from river import tree

    model = tree.HoeffdingTreeClassifier(
        grace_period=2,
        max_depth=3,
        leaf_prediction="mc",
        split_criterion="gini",
    )
    rows = _binary_rows() + [({"x": 0.5, "bias": 1.0}, True), ({"x": -0.5, "bias": 1.0}, False)]
    _repeat_learn(model, rows, repeats, weighted=True)
    proba = model.predict_proba_one({"x": 1.25, "bias": 1.0})
    if not proba or not math.isclose(sum(proba.values()), 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise AssertionError(f"unexpected tree probabilities: {proba!r}")
    return {"classes": sorted(map(str, proba)), "height": getattr(model, "height", None)}


def check_wrappers(repeats):
    from river import linear_model, multiclass, multioutput, optim

    ovr = multiclass.OneVsRestClassifier(
        linear_model.LogisticRegression(optimizer=optim.SGD(0.2), clip_gradient=10.0)
    )
    rows = [
        ({"x": 2.0, "y": 0.0}, "right"),
        ({"x": -2.0, "y": 0.0}, "left"),
        ({"x": 0.0, "y": 2.0}, "up"),
        ({"x": 1.5, "y": 0.2}, "right"),
        ({"x": -1.5, "y": 0.1}, "left"),
        ({"x": 0.1, "y": 1.5}, "up"),
    ]
    _repeat_learn(ovr, rows, repeats, weighted=False)
    proba = ovr.predict_proba_one({"x": 2.5, "y": 0.0})
    if set(proba) != {"left", "right", "up"} or not math.isclose(sum(proba.values()), 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise AssertionError(f"unexpected one-vs-rest probabilities: {proba!r}")

    base_reg = linear_model.LinearRegression(
        optimizer=optim.SGD(0.03),
        intercept_lr=0.03,
        clip_gradient=10.0,
    )
    per_output = multioutput.PerOutputRegressor(model=base_reg)
    multi_rows = [
        ({"x": -1.0}, {"a": -1.0, "b": 1.0}),
        ({"x": 0.0}, {"a": 0.0, "b": 0.0}),
        ({"x": 1.0}, {"a": 1.0, "b": -1.0}),
    ]
    _repeat_learn(per_output, multi_rows, repeats, weighted=False)
    pred = per_output.predict_one({"x": 0.5})
    if set(pred) != {"a", "b"} or not all(isinstance(v, float) for v in pred.values()):
        raise AssertionError(f"unexpected multioutput prediction: {pred!r}")
    return {"ovr_labels": sorted(proba), "multioutput_keys": sorted(pred)}


def check_model_selection(repeats):
    from river import linear_model, metrics, model_selection, optim

    models = [
        linear_model.LogisticRegression(optimizer=optim.SGD(0.2), clip_gradient=10.0),
        linear_model.LogisticRegression(optimizer=optim.SGD(0.02), clip_gradient=10.0),
    ]
    selector = model_selection.SuccessiveHalvingClassifier(
        models=models,
        metric=metrics.Accuracy(),
        budget=max(8, repeats * len(_binary_rows())),
        eta=2,
    )
    _repeat_learn(selector, _binary_rows(), repeats, weighted=False)
    proba = selector.predict_proba_one({"x": 1.0, "bias": 1.0})
    if set(proba) != {False, True}:
        raise AssertionError(f"unexpected selector probabilities: {proba!r}")
    return {"best_model": selector.best_model.__class__.__name__, "classes": sorted(map(str, proba))}


def check_compat(repeats, mode):
    if mode == "skip":
        return {"status": "skipped"}
    try:
        from sklearn import linear_model as sk_linear_model
        from river import compat
    except Exception as exc:
        if mode == "require":
            raise
        return {"status": "skipped", "reason": exc.__class__.__name__}
    if not hasattr(compat, "convert_sklearn_to_river"):
        if mode == "require":
            raise AssertionError("river.compat conversion functions are unavailable")
        return {"status": "skipped", "reason": "compat converters unavailable"}

    model = compat.convert_sklearn_to_river(
        sk_linear_model.SGDClassifier(loss="log_loss", random_state=42),
        classes=[False, True],
    )
    _repeat_learn(model, _binary_rows(), repeats, weighted=False)
    proba = model.predict_proba_one({"x": 1.0, "bias": 1.0})
    if set(proba) != {False, True}:
        raise AssertionError(f"unexpected sklearn-to-river probabilities: {proba!r}")
    return {"status": "ok", "classes": sorted(map(str, proba))}


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run tiny offline River supervised-model smoke checks.")
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=["all", "linear", "tree", "wrappers", "model-selection", "compat"],
        default=["all"],
    )
    parser.add_argument("--repeats", type=int, default=8)
    parser.add_argument("--compat", choices=["try", "skip", "require"], default="try")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.repeats < 1:
        raise SystemExit("--repeats must be positive")
    checks = ["linear", "tree", "wrappers", "model-selection", "compat"] if "all" in args.checks else args.checks
    results = {}
    for name in checks:
        if name == "linear":
            results[name] = check_linear(args.repeats)
        elif name == "tree":
            results[name] = check_tree(args.repeats)
        elif name == "wrappers":
            results[name] = check_wrappers(args.repeats)
        elif name == "model-selection":
            results[name] = check_model_selection(args.repeats)
        elif name == "compat":
            results[name] = check_compat(args.repeats, args.compat)
    print(json.dumps({"ok": True, "checks": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
