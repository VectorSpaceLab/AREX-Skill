#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from collections.abc import Callable
from typing import Any


Result = dict[str, Any]


def passed(section: str, **details: Any) -> Result:
    return {"section": section, "status": "passed", **details}


def skipped(section: str, reason: str) -> Result:
    return {"section": section, "status": "skipped", "reason": reason}


def require_river() -> Result | None:
    try:
        river = importlib.import_module("river")
    except Exception as exc:
        return {
            "section": "river-import",
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
        }
    return passed("river-import", version=getattr(river, "__version__", "unknown"))


def check_drift() -> Result:
    section = "drift"
    try:
        from river import drift, naive_bayes
    except Exception as exc:
        return skipped(section, f"drift modules unavailable: {type(exc).__name__}: {exc}")

    detector = drift.PageHinkley(min_instances=5, threshold=5.0, mode="up")
    detected_at = None
    for i, value in enumerate([0.0] * 30 + [10.0] * 30):
        detector.update(value)
        if detector.drift_detected and detected_at is None:
            detected_at = i
    assert detected_at is not None

    retraining = drift.DriftRetrainingClassifier(
        model=naive_bayes.GaussianNB(),
        drift_detector=drift.binary.DDM(warm_start=2),
    )
    samples = [
        ({"x": 0.0}, False),
        ({"x": 0.1}, False),
        ({"x": 0.2}, False),
        ({"x": 1.0}, True),
        ({"x": 1.1}, True),
    ]
    for x, y in samples:
        retraining.learn_one(x, y)
    proba = retraining.predict_proba_one({"x": 0.2})
    assert proba

    return passed(
        section,
        page_hinkley_detected_at=detected_at,
        retraining_classes=sorted(map(str, proba)),
        detector_has_warning=hasattr(retraining.drift_detector, "warning_detected"),
    )


def check_anomaly() -> Result:
    section = "anomaly"
    try:
        from river import anomaly
    except Exception as exc:
        return skipped(section, f"anomaly module unavailable: {type(exc).__name__}: {exc}")

    detector = anomaly.HalfSpaceTrees(n_trees=5, height=3, window_size=4, seed=0)
    for x in [
        {"x": 0.10, "y": 0.10},
        {"x": 0.12, "y": 0.11},
        {"x": 0.09, "y": 0.10},
        {"x": 0.11, "y": 0.12},
    ]:
        detector.learn_one(x)

    normal_score = detector.score_one({"x": 0.10, "y": 0.11})
    outlier_score = detector.score_one({"x": 0.95, "y": 0.95})
    assert outlier_score > normal_score

    threshold = (normal_score + outlier_score) / 2
    filtered = anomaly.ThresholdFilter(detector, threshold=threshold)
    assert filtered.classify(normal_score) is False
    assert filtered.classify(outlier_score) is True

    supervised = anomaly.GaussianScorer(grace_period=2)
    for y in [0.0, 0.1, -0.1, 0.05, 0.0]:
        supervised.learn_one(None, y)
    target_normal = supervised.score_one(None, 0.0)
    target_outlier = supervised.score_one(None, 1.0)
    assert target_outlier > target_normal

    return passed(
        section,
        normal_score=float(normal_score),
        outlier_score=float(outlier_score),
        target_normal_score=float(target_normal),
        target_outlier_score=float(target_outlier),
    )


def check_cluster() -> Result:
    section = "cluster"
    try:
        from river import cluster, metrics
    except Exception as exc:
        return skipped(section, f"cluster modules unavailable: {type(exc).__name__}: {exc}")

    model = cluster.KMeans(n_clusters=2, halflife=0.4, sigma=3, seed=0)
    silhouette = metrics.Silhouette()
    adjusted_rand = metrics.AdjustedRand()
    stream = [
        ({0: -10.0, 1: -10.0}, 0),
        ({0: -9.5, 1: -10.5}, 0),
        ({0: -10.5, 1: -9.5}, 0),
        ({0: 10.0, 1: 10.0}, 1),
        ({0: 9.5, 1: 10.5}, 1),
        ({0: 10.5, 1: 9.5}, 1),
    ]
    for x, y_true in stream:
        model.learn_one(x)
        y_pred = model.predict_one(x)
        silhouette.update(x, y_pred, model.centers)
        adjusted_rand.update(y_true, y_pred)

    sil = float(silhouette.get())
    ari = float(adjusted_rand.get())
    assert math.isfinite(sil)
    assert math.isfinite(ari)

    return passed(section, silhouette=sil, adjusted_rand=ari, centers=len(model.centers))


def check_time_series() -> Result:
    section = "time-series"
    try:
        from river import evaluate, metrics, time_series
    except Exception as exc:
        return skipped(section, f"time-series modules unavailable: {type(exc).__name__}: {exc}")

    values = [10.0, 12.0, 13.0, 15.0, 16.0, 18.0]
    model = time_series.HoltWinters(alpha=0.5)
    for y in values[:4]:
        model.learn_one(y)
    forecast = model.forecast(horizon=2)
    assert len(forecast) == 2

    metric = evaluate.evaluate(
        dataset=[(None, y) for y in values],
        model=time_series.HoltWinters(alpha=0.5),
        metric=metrics.MAE(),
        horizon=2,
    )
    horizon_values = [float(v) for v in metric.get()]
    assert len(horizon_values) == 2
    assert all(math.isfinite(v) for v in horizon_values)

    return passed(section, forecast=[float(v) for v in forecast], horizon_mae=horizon_values)


def check_bandit() -> Result:
    section = "bandit"
    try:
        from river import bandit
    except Exception as exc:
        return skipped(section, f"bandit module unavailable: {type(exc).__name__}: {exc}")

    arms = ["A", "B"]
    policy = bandit.EpsilonGreedy(epsilon=0.0, burn_in=1, seed=0)
    for _ in range(2):
        arm = policy.pull(arms)
        policy.update(arm, 1.0 if arm == "A" else 0.0)
    assert policy.ranking[0] == "A"

    history = [(arms, None, "A", 1.0) for _ in range(3)]
    reward_stat, n_used = bandit.evaluate_offline(
        policy=bandit.EpsilonGreedy(epsilon=0.0, seed=0),
        history=history,
    )
    assert n_used == len(history)
    assert reward_stat.get() == len(history)

    gym_status: Result
    try:
        gym = importlib.import_module("gymnasium")
    except Exception as exc:
        gym_status = {"status": "skipped", "reason": f"gymnasium unavailable: {type(exc).__name__}"}
    else:
        env_ids = [str(k) for k in gym.envs.registry if str(k).startswith("river_bandits")]
        gym_status = {"status": "available", "river_env_count": len(env_ids)}

    return passed(
        section,
        online_best_arm=policy.ranking[0],
        offline_reward=float(reward_stat.get()),
        offline_samples_used=int(n_used),
        optional_gymnasium=gym_status,
    )


def check_reco() -> Result:
    section = "reco"
    try:
        from river import reco
    except Exception as exc:
        return skipped(section, f"reco module unavailable: {type(exc).__name__}: {exc}")

    model = reco.Baseline()
    interactions = [
        ({"user": "Alice", "item": "Superman"}, 1.0),
        ({"user": "Alice", "item": "Terminator"}, 0.0),
        ({"user": "Bob", "item": "Superman"}, 1.0),
        ({"user": "Bob", "item": "Terminator"}, 0.0),
    ]
    for x, y in interactions:
        model.learn_one(**x, y=y)

    items = {"Superman", "Terminator"}
    ranked = model.rank("Bob", items)
    assert set(ranked) == items
    assert ranked[0] == "Superman"
    score = model.predict_one(user="Bob", item="Superman")

    return passed(section, top_item=ranked[0], score=float(score), contextual=model.is_contextual)


def check_facto() -> Result:
    section = "facto"
    try:
        from river import facto
    except Exception as exc:
        return skipped(section, f"facto module unavailable: {type(exc).__name__}: {exc}")

    model = facto.FMClassifier(n_factors=3, seed=0)
    samples = [
        ({"user": "Tom", "item": "politics"}, True),
        ({"user": "Tom", "item": "sports"}, False),
        ({"user": "Anna", "item": "sports"}, True),
        ({"user": "Anna", "item": "music"}, False),
    ]
    for x, y in samples:
        model.learn_one(x, y)

    probe = {"user": "Tom", "item": "politics"}
    proba = model.predict_proba_one(probe)
    assert set(proba) == {False, True}
    report = model.debug_one(probe)
    assert "Intercept" in report

    return passed(section, true_probability=float(proba[True]), debug_contains_intercept=True)


def check_imbalanced() -> Result:
    section = "imbalanced"
    try:
        from river import imblearn, naive_bayes
    except Exception as exc:
        return skipped(section, f"imblearn modules unavailable: {type(exc).__name__}: {exc}")

    model = imblearn.RandomOverSampler(
        classifier=naive_bayes.GaussianNB(),
        desired_dist={False: 0.5, True: 0.5},
        seed=0,
    )
    samples = [
        ({"x": 0.0}, False),
        ({"x": 0.1}, False),
        ({"x": 0.2}, False),
        ({"x": 1.0}, True),
    ]
    for x, y in samples:
        model.learn_one(x, y)
    pred = model.predict_one({"x": 0.9})
    assert pred in {False, True, None}

    return passed(
        section,
        wrapper=type(model).__name__,
        wrapped_classifier=type(model.classifier).__name__,
        prediction=None if pred is None else bool(pred),
    )


def check_proba() -> Result:
    section = "proba"
    try:
        from river import proba
    except Exception as exc:
        return skipped(section, f"proba module unavailable: {type(exc).__name__}: {exc}")

    gaussian = proba.Gaussian()
    gaussian.update(1.0)
    gaussian.update(3.0)
    assert gaussian.n_samples == 2
    assert math.isclose(gaussian.mu, 2.0)

    beta = proba.Beta()
    beta.update(True)
    beta.update(False)
    assert math.isclose(beta.mode, 0.5)

    multinomial = proba.Multinomial(["red", "red", "blue"])
    multinomial.update("red")
    assert multinomial.mode == "red"
    assert math.isclose(multinomial("red"), 0.75)

    return passed(
        section,
        gaussian_mu=float(gaussian.mu),
        beta_mode=float(beta.mode),
        red_probability=float(multinomial("red")),
    )


SECTION_FUNCTIONS: dict[str, Callable[[], Result]] = {
    "drift": check_drift,
    "anomaly": check_anomaly,
    "cluster": check_cluster,
    "time-series": check_time_series,
    "bandit": check_bandit,
    "reco": check_reco,
    "facto": check_facto,
    "imbalanced": check_imbalanced,
    "proba": check_proba,
}


def run_section(name: str) -> Result:
    try:
        return SECTION_FUNCTIONS[name]()
    except Exception as exc:
        return {"section": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny synthetic River specialized-workflow checks."
    )
    parser.add_argument(
        "--section",
        action="append",
        choices=["all", *SECTION_FUNCTIONS.keys()],
        help="Section to run. Repeat for multiple sections. Defaults to all sections.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = args.section or ["all"]
    section_names = list(SECTION_FUNCTIONS) if "all" in selected else list(dict.fromkeys(selected))

    import_result = require_river()
    if import_result is None:
        results = []
    elif import_result["status"] == "failed":
        results = [import_result]
        section_names = []
    else:
        results = [import_result]

    results.extend(run_section(name) for name in section_names)
    ok = all(result["status"] != "failed" for result in results)
    summary = {"ok": ok, "results": results}

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("specialized-workflows smoke check")
        for result in results:
            line = f"- {result['section']}: {result['status']}"
            if result["status"] == "skipped":
                line += f" ({result['reason']})"
            if result["status"] == "failed":
                line += f" ({result['error']})"
            print(line)
        print(json.dumps(summary, indent=2, sort_keys=True))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
