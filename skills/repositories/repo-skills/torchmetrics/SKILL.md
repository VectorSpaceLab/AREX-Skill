---
name: torchmetrics
description: "Use TorchMetrics to choose, inspect, and combine metric families
  for PyTorch evaluation, including core API, domain metrics, model-based
  metrics, and wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TorchMetrics

TorchMetrics is a metric library for PyTorch evaluation.
Use this skill when the request is about choosing, calling, combining, or debugging TorchMetrics APIs rather than about training a model itself.

## Start here

- Read [references/metric-selection-cheatsheet.md](references/metric-selection-cheatsheet.md) to map a user request to the right sub-skill.
- Run [scripts/check_torchmetrics_environment.py](scripts/check_torchmetrics_environment.py) with `--device auto` to confirm the install and core imports.
- Read [references/repo-provenance.md](references/repo-provenance.md) when you need freshness, source-version, or staleness checks.
- Read [references/troubleshooting.md](references/troubleshooting.md) when install, import, backend, device, distributed, plotting, or model-download problems appear.

## Route map

- `core-api` — `Metric`, functional versus module metrics, `update` / `compute` / `forward` / `reset`, custom metric state, Lightning logging, DDP behavior, persistence.
- `basic-metric-domains` — classification, regression, retrieval, clustering, nominal, and other tensor-only metric families.
- `vision-detection-metrics` — image quality, segmentation, detection, and panoptic metrics.
- `audio-text-metrics` — audio and speech quality metrics plus no-download text metrics such as ROUGE, WER, CER, BLEU, SacreBLEU, and Perplexity.
- `model-based-metrics` — BERTScore, InfoLM, CLIPScore, CLIP-IQA, FID/KID/LPIPS/DISTS/ARNIQA/PPL, DNSMOS, NISQA, VMAF, and similar metrics that need pretrained assets or external model planning.
- `collections-wrappers-plotting` — `MetricCollection`, wrappers, trackers, and plotting.

## How to choose

1. If the task is about implementing or debugging a custom `Metric`, start with `core-api`.
2. If the task names a familiar metric family such as accuracy, F1, MSE, nDCG, or Cramer's V, use the sub-skill that owns that family.
3. If the task is about combining metrics, renaming outputs, tracking metrics over epochs, or plotting results, use `collections-wrappers-plotting`.
4. If the metric may instantiate a pretrained model, feature extractor, or large optional asset, route to `model-based-metrics`.
5. If a request spans families, choose the primary metric family first, then follow the route back to `core-api` or `collections-wrappers-plotting` as needed.

## Install guidance

TorchMetrics has no verified console CLI. Install it from Python:

```bash
pip install torchmetrics
```

Then add only the extra that matches the route you chose when needed, for example `torchmetrics[audio]`, `torchmetrics[image]`, `torchmetrics[text]`, `torchmetrics[detection]`, `torchmetrics[multimodal]`, `torchmetrics[video]`, `torchmetrics[visual]`, or `torchmetrics[clustering]`.
Avoid `torchmetrics[all]` unless you truly need a very broad evaluation environment.

## Fast checks

- `python -c "import torchmetrics; print(torchmetrics.__version__)"`
- `python scripts/check_torchmetrics_environment.py --device auto`

## Common signals

- `Metric`, `add_state`, `compute_with_cache`, `LightningModule`, or `DDP` -> `core-api`
- `Accuracy`, `F1`, `MSE`, `nDCG`, `ClusterAccuracy`, or `CramersV` -> `basic-metric-domains`
- `PSNR`, `DiceScore`, `MeanAveragePrecision`, or `PanopticQuality` -> `vision-detection-metrics`
- `SNR`, `PESQ`, `WER`, `ROUGE`, or `Perplexity` -> `audio-text-metrics`
- `BERTScore`, `CLIPScore`, `FID`, `LPIPS`, `DNSMOS`, or `VMAF` -> `model-based-metrics`
- `MetricCollection`, `ClasswiseWrapper`, `MetricTracker`, or `.plot()` -> `collections-wrappers-plotting`
