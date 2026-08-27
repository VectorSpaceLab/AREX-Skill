# TorchMetrics metric selection cheat sheet

Use this as the quick index when a user asks for a metric but does not name the right family.

| User intent | Start with | Why |
| --- | --- | --- |
| Implement a custom metric, fix a Lightning logging issue, or understand `update`/`compute`/`reset` | `core-api` | Covers the shared Metric lifecycle, state handling, device behavior, and Lightning/DDD rules. |
| Compare predictions with standard tensor metrics such as accuracy, F1, MSE, nDCG, clustering scores, or nominal association scores | `basic-metric-domains` | Owns the familiar tensor-only metric families. |
| Evaluate image quality, segmentation masks, detection boxes/masks, or panoptic scenes | `vision-detection-metrics` | Owns the image, segmentation, detection, and panoptic APIs and shapes. |
| Score audio waveforms, speech separation outputs, ASR transcripts, summaries, translations, or logits | `audio-text-metrics` | Owns audio/speech quality metrics and no-download text metrics. |
| Use BERTScore, CLIPScore, FID, LPIPS, DNSMOS, VMAF, or any metric that loads pretrained weights or external assets | `model-based-metrics` | Owns model-backed metrics and their cache, device, and download constraints. |
| Combine metrics, rename outputs, track metrics over epochs, or plot results | `collections-wrappers-plotting` | Owns `MetricCollection`, wrappers, trackers, and plotting helpers. |

## Signal words that usually decide the route

- **Core API**: `Metric`, `add_state`, `persistent`, `sync_on_compute`, `compute_with_cache`, `LightningModule`, `DDP`
- **Basic domains**: `Accuracy`, `AUROC`, `MSE`, `nDCG`, `ClusterAccuracy`, `CramersV`, `FleissKappa`
- **Vision/detection**: `PSNR`, `SSIM`, `DiceScore`, `MeanIoU`, `MeanAveragePrecision`, `PanopticQuality`
- **Audio/text**: `SNR`, `SDR`, `PESQ`, `STOI`, `ROUGE`, `BLEU`, `WER`, `CER`, `Perplexity`
- **Model-based**: `BERTScore`, `CLIPScore`, `CLIP-IQA`, `FID`, `KID`, `LPIPS`, `DNSMOS`, `NISQA`, `VMAF`
- **Wrappers/plotting**: `MetricCollection`, `ClasswiseWrapper`, `BootStrapper`, `MetricTracker`, `plot`, `together=True`

## Decision rule

If a request mixes families, choose the metric family that owns the input shape or backend first, then add `core-api` or `collections-wrappers-plotting` only for the shared state or composition behavior.
