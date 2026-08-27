---
name: model-based-metrics
description: "Use TorchMetrics metrics that load pretrained models, feature
  extractors, external weights, caches, or download-backed assets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model-Based Metrics

Use this sub-skill when a TorchMetrics metric depends on pretrained weights, a model or tokenizer, external feature extractors, a cache, or a network-backed asset.

## Route map

- Read [references/model-based-api.md](references/model-based-api.md) when you need constructor arguments, supported model names, cache/device rules, or output-shape details for model-backed metrics.
- Read [references/model-based-workflows.md](references/model-based-workflows.md) when you need copyable usage patterns or planning guidance for BERTScore, CLIPScore, CLIP-IQA, FID/KID, LPIPS/DISTS/ARNIQA, DNSMOS, NISQA, VMAF, or related metrics.
- Read [references/troubleshooting.md](references/troubleshooting.md) when import succeeds but model loading, cache lookup, device placement, or optional dependency handling fails.
- Run [scripts/model_based_import_check.py](scripts/model_based_import_check.py) for a no-download import and signature check that confirms the installed package exposes the expected classes.

## What this sub-skill covers

- Text model-based metrics: `BERTScore`, `InfoLM`.
- Multimodal CLIP metrics: `CLIPScore`, `CLIPImageQualityAssessment`.
- Image feature/model metrics: `FrechetInceptionDistance`, `KernelInceptionDistance`, `InceptionScore`, `MemorizationInformedFrechetInceptionDistance`, `LearnedPerceptualImagePatchSimilarity`, `DeepImageStructureAndTextureSimilarity`, `ARNIQA`, `PerceptualPathLength`.
- Audio model-backed metrics: `DeepNoiseSuppressionMeanOpinionScore`, `NonIntrusiveSpeechQualityAssessment`.
- Video and facial/multimodal metrics: `VideoMultiMethodAssessmentFusion`, `LipVertexError`.

## Route elsewhere

- Read `../core-api/SKILL.md` for the shared Metric lifecycle, distributed sync, persistence, and Lightning logging.
- Read `../vision-detection-metrics/SKILL.md` for PSNR, SSIM, Dice, MeanIoU, mAP, and other non-model image/detection metrics.
- Read `../audio-text-metrics/SKILL.md` for SNR, PESQ, WER, ROUGE, BLEU, SacreBLEU, and Perplexity.
- Read `../collections-wrappers-plotting/SKILL.md` for MetricCollection, wrappers, trackers, and plotting.

## Quick use

1. Check whether the user actually needs a model-backed metric or only a simple tensor metric.
2. Decide which pretrained model, tokenizer, or feature extractor to use, and whether a cache is already available.
3. Check whether the requested environment can satisfy downloads, device placement, and memory use.
4. Prefer no-download import/signature checks when you only need to document or inspect the API.

## Fast checks

- `python scripts/model_based_import_check.py`
- `python -c "from torchmetrics.text import BERTScore; import inspect; print(inspect.signature(BERTScore.__init__))"`

## Common signals

- `model_name_or_path`, `model`, `user_tokenizer`, `user_forward_fn`, `baseline_path`, `baseline_url`, `rescale_with_baseline`, `truncation` -> BERTScore or InfoLM
- `CLIPScore`, `CLIPImageQualityAssessment`, `openai/clip-...` -> CLIP metrics
- `torch_fidelity`, `feature extractor`, `InceptionScore`, `FID`, `KID` -> image feature metrics
- `piq`, `torchvision` weights, `LPIPS`, `DISTS`, `ARNIQA`, `PerceptualPathLength` -> image model-based metrics
- `librosa`, `onnxruntime`, `requests`, `DNSMOS`, `NISQA` -> audio model-based metrics
- `vmaf_torch`, `VideoMultiMethodAssessmentFusion` -> video quality metric
