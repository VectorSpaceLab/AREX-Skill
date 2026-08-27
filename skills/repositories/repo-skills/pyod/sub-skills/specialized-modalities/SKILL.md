---
name: specialized-modalities
description: "Operate PyOD's time-series, graph, embedding/text/image/audio,
  multimodal, and torch-backed modality workflows with precise optional-backend
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# PyOD Specialized Modalities

Use this sub-skill when the user is working outside ordinary numeric tabular anomaly detection: time series, graphs, text/image/audio embeddings, multimodal fusion, or torch-backed neural detectors. Keep basic tabular `fit`/`predict` detector usage routed to `classic-detectors`, ADEngine/CLI/MCP lifecycle work to `automated-lifecycle`, and persistence/thresholding/combination operations to `model-operations`.

## Quick route

- Time series arrays, windowing, transductive detectors, or `TimeSeriesOD`, `KShape`, `MatrixProfile`, `SpectralResidual`, `SAND`, `LSTMAD`, `AnomalyTransformer`: read [time-series.md](references/time-series.md). Run [scripts/time_series_smoke.py](scripts/time_series_smoke.py) for a deterministic CPU-only sanity check.
- PyTorch Geometric node-anomaly workflows, `Data(x, edge_index)`, graph detector selection, SCAN's structure-only path, or `pyod[graph]` installs: read [graph.md](references/graph.md).
- `EmbeddingOD`, `MultiModalOD`, text/image/audio presets, local/custom encoders, audio features, `AudioAE`, and modality fusion: read [embedding-audio.md](references/embedding-audio.md).
- Optional extras, torch/neural detector backend choices, credentials, CPU/GPU cautions, and install variants: read [optional-backends.md](references/optional-backends.md). Run [scripts/modality_backend_probe.py](scripts/modality_backend_probe.py) before giving install/remediation advice.
- Errors, shape mismatches, missing extras, transductive API surprises, graph-data failures, neural small-data issues, and credential/cache problems: read [troubleshooting.md](references/troubleshooting.md).

## Operating rules

1. Verify the installed optional backend before recommending a modality workflow. Core PyOD is enough for CPU time-series detectors except `LSTMAD` and `AnomalyTransformer`; graph, embedding, OpenAI, HuggingFace image/text, audio, and most neural detectors need extras.
2. Do not claim GPU support or speed unless the current runtime has actually been probed. PyOD torch models can usually run on CPU; set explicit CPU devices for reproducible smoke tests when a class exposes a device parameter.
3. Treat all PyOD graph detectors and `MatrixProfile` as transductive: use `decision_scores_` and `labels_` after `fit()` rather than out-of-sample `predict()`.
4. For embedding workflows, remember that `EmbeddingOD` defaults to detector `LUNAR`, which is torch-backed. If torch is absent, choose a non-torch detector such as `KNN`, `LOF`, `ECOD`, or `IForest`, or install the `torch` extra.
5. For neural/deep detectors on small data, reduce `batch_size`, epochs, model width/depth, and prefer deterministic CPU smoke checks before expensive runs.
