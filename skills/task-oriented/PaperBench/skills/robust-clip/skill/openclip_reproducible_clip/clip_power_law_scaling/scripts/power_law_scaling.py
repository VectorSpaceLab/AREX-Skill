import argparse
import json
import math


def _frontier(records, metric):
    ordered = sorted(records, key=lambda item: item["total_compute"])
    best = float("inf")
    kept = []
    for item in ordered:
        value = float(item[metric])
        if value < best:
            kept.append(item)
            best = value
    return kept


def fit_power_law(records, metric="retrieval_error", use_frontier=True):
    selected = [dict(item) for item in records if float(item.get("total_compute", 0)) > 0 and float(item.get(metric, 0)) > 0]
    if use_frontier:
        selected = _frontier(selected, metric)
    if len(selected) < 2:
        raise ValueError("at least two positive points are required")
    xs = [math.log(float(item["total_compute"])) for item in selected]
    ys = [math.log(float(item[metric])) for item in selected]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        raise ValueError("compute values must vary")
    exponent = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
    intercept = y_mean - exponent * x_mean
    preds_log = [intercept + exponent * x for x in xs]
    ss_res = sum((y - pred) ** 2 for y, pred in zip(ys, preds_log))
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r2 = 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
    predictions = [math.exp(value) for value in preds_log]
    return {
        "schema_version": 1,
        "metric": metric,
        "point_count": len(selected),
        "coefficient": math.exp(intercept),
        "exponent": exponent,
        "log_power_law_r2": r2,
        "predictions": predictions,
        "frontier_records": selected,
        "negative_exponent": exponent < 0
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--metric", default="retrieval_error")
    parser.add_argument("--output", required=True)
    parser.add_argument("--no-frontier", action="store_true")
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    records = payload.get("records", payload)
    result = fit_power_law(records, args.metric, not args.no_frontier)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

if __name__ == "__main__":
    main()
