# Model-Based Metrics API

This reference covers TorchMetrics metrics that load pretrained models, feature extractors, or other external assets.

## Text model-based metrics

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| BERTScore | `BERTScore` / `bert_score` | Predicted and target strings | `model_name_or_path`, `num_layers`, `all_layers`, `model`, `user_tokenizer`, `user_forward_fn`, `idf`, `device`, `max_length`, `batch_size`, `num_threads`, `return_hash`, `lang`, `rescale_with_baseline`, `baseline_path`, `baseline_url`, `truncation` | Dict of precision/recall/F1 | Can use default Transformer models or a supplied model/tokenizer pair. |
| InfoLM | `InfoLM` / `inform` | Predicted and target strings | `model_name_or_path`, `model`, `user_tokenizer`, `user_forward_fn`, `device`, `max_length`, `batch_size`, `num_threads`, `idf`, `return_hash`, `normalize`-style arguments depending on version | Dict or scalar-like outputs | Shared Hugging Face transformer-planning surface with BERTScore. |

## CLIP and multimodal metrics

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| CLIPScore | `CLIPScore` / `clip_score` | Image tensor and caption text | `model_name_or_path` | Scalar tensor | Default model names include OpenAI CLIP and Jina CLIP variants. |
| CLIP Image Quality Assessment | `CLIPImageQualityAssessment` / `clip_image_quality_assessment` | Image tensor and quality prompts | `model_name_or_path`, `data_range`, `prompts` | Dict or scalar tensor | The default `clip_iqa` path may use `piq` internally. |
| LipVertexError | `LipVertexError` | Landmark or mouth-region geometry | `mouth_map`, `validate_args` | Scalar tensor | Multimodal face/lip geometry metric; not a pretrained model load, but grouped with multimodal metrics. |

## Image feature and perceptual metrics

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| Frechet Inception Distance | `FrechetInceptionDistance` / `frechet_inception_distance` | Real and fake image batches | `feature`, `normalize`, `reset_real_features` | Scalar tensor | Uses pretrained feature extraction. |
| Kernel Inception Distance | `KernelInceptionDistance` / `kernel_inception_distance` | Real and fake image batches | `feature`, `normalize`, `subset_size` | Scalar tensor | Requires `torch_fidelity`. |
| Inception Score | `InceptionScore` / `inception_score` | Image batches | `feature`, `splits`, `normalize` | Scalar tensor | Pretrained feature extractor based. |
| Memorization-Informed FID | `MemorizationInformedFrechetInceptionDistance` / `memorization_informed_frechet_inception_distance` | Real and fake image batches | `feature`, `reset_real_features`, `normalize`, `cosine_distance_eps` | Scalar tensor | Uses FID-style feature extraction with memorization-aware adjustments. |
| LPIPS | `LearnedPerceptualImagePatchSimilarity` / `learned_perceptual_image_patch_similarity` | Matching image tensors | `net_type`, `normalize`, `reduction` | Scalar or per-sample tensor | Uses pretrained CNN feature backbones from torchvision. |
| DISTS | `DeepImageStructureAndTextureSimilarity` / `deep_image_structure_and_texture_similarity` | Matching image tensors | `reduction` | Scalar or per-sample tensor | Uses torchvision features. |
| ARNIQA | `ARNIQA` / `arniqa` | Image tensors | `model_name_or_path`, `data_range`, `normalize` | Scalar tensor | Uses torchvision and a pretrained quality model. |
| Perceptual Path Length | `PerceptualPathLength` / `perceptual_path_length` | Image tensors, usually latent interpolation samples | `feature_extractor`, `normalize`, `reduction` | Scalar tensor | Uses torchvision-based feature extraction. |

## Audio and video model-backed metrics

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| DNSMOS | `DeepNoiseSuppressionMeanOpinionScore` / `deep_noise_suppression_mean_opinion_score` | Audio waveform tensors | `fs`, `personalized`, `num_threads`, backend/model download parameters | Scalar tensor | Needs `librosa`, `onnxruntime`, and `requests`; may fetch a model/session. |
| NISQA | `NonIntrusiveSpeechQualityAssessment` / `non_intrusive_speech_quality_assessment` | Audio waveform tensors | `fs`, model/download parameters | Scalar tensor | Needs `librosa` and `requests`; model planning is network-sensitive. |
| Video VMAF | `VideoMultiMethodAssessmentFusion` / `video_multi_method_assessment_fusion` | Video feature tensors or clips | `features` | Scalar tensor | Uses `vmaf_torch` and can operate in feature mode without downloading model weights. |

## General planning rules

- Prefer no-download import and signature checks when the task is about API inspection rather than runtime scoring.
- Treat `model_name_or_path`, `baseline_url`, `feature`, `normalize`, `reset_real_features`, and similar arguments as planning points that can change memory, cache, and network requirements.
- Keep model-backed metrics separate from the simple tensor metrics in other sub-skills so future agents do not confuse a pretrained-model dependency with a plain scoring function.
