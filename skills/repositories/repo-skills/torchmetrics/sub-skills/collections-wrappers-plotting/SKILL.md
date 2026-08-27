---
name: collections-wrappers-plotting
description: "Compose, transform, track, bootstrap, and plot TorchMetrics
  metrics with collections and wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Collections, Wrappers, and Plotting

Use this sub-skill when the task is mainly about combining metrics, transforming metric inputs, tracking values over time, bootstrapping confidence intervals, or plotting results.

## Route map

- Read [references/collections-wrappers-api.md](references/collections-wrappers-api.md) when you need constructor arguments, return shapes, and ownership rules for `MetricCollection`, aggregation metrics, or wrappers.
- Read [references/plotting-and-tracking.md](references/plotting-and-tracking.md) when you need patterns for epoch tracking, train/validation prefixes, classwise outputs, bootstrap summaries, or headless plotting.
- Read [references/troubleshooting.md](references/troubleshooting.md) when collection keys collide, member update signatures differ, wrapper outputs are not scalar, plotting fails, or `MetricTracker` cannot infer maximize direction.
- Run [scripts/collections_wrappers_smoke.py](scripts/collections_wrappers_smoke.py) for a no-download check of collections, wrappers, tracking, and optional Agg plotting.

## What this sub-skill covers

- `MetricCollection` from dicts, lists, nested collections, prefixes, postfixes, cloning, `compute_groups`, and filtered keyword routing.
- Wrappers: `ClasswiseWrapper`, `BootStrapper`, `MinMaxMetric`, `MultioutputWrapper`, `MultitaskWrapper`, `MetricTracker`, `Running`, `FeatureShare`, `BinaryTargetTransformer`, `LambdaInputTransformer`, and `MetricInputTransformer`.
- Aggregation helpers such as `MeanMetric`, `SumMetric`, `RunningMean`, and `RunningSum` when the user wants scalar aggregation.
- Plotting with `.plot()`, `val=`, `ax=`, collection plotting, `together=True`, and non-interactive matplotlib backends.

## Route elsewhere

- Read `../core-api/SKILL.md` for Metric lifecycle, custom metrics, device movement, DDP synchronization, persistence, or Lightning reset rules.
- Read `../basic-metric-domains/SKILL.md`, `../vision-detection-metrics/SKILL.md`, or `../audio-text-metrics/SKILL.md` when the task is choosing a metric family.
- Read `../model-based-metrics/SKILL.md` when the metric being plotted or wrapped needs pretrained model assets.

## Quick use

1. Use `MetricCollection` when several metrics share the same input signature.
2. Use a dict rather than a list when metric names need to be stable or duplicate metric classes are present.
3. Clone collections with `prefix=` or `postfix=` for train/validation/test streams.
4. Check whether wrapper outputs are scalar tensors, dicts, lists, or class vectors before logging or plotting.
5. In headless environments, set matplotlib to an Agg backend before calling `.plot()`.

## Fast checks

- `python scripts/collections_wrappers_smoke.py`
- `python scripts/collections_wrappers_smoke.py --plot ./torchmetrics-plot.png`

## Common signals

- `MetricCollection`, `clone`, `prefix`, `postfix`, `compute_groups` -> collection guidance
- `ClasswiseWrapper`, labels, per-class output names -> classwise wrapper guidance
- `BootStrapper`, confidence intervals, quantiles -> bootstrap wrapper guidance
- `MetricTracker`, best epoch, `compute_all`, `best_metric` -> tracking guidance
- `.plot()`, `val`, `ax`, `together=True`, `matplotlib` -> plotting guidance
