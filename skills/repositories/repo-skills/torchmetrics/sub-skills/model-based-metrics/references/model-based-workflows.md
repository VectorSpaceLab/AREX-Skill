# Model-Based Metric Workflows

## 1) No-download inspection workflow

Use this when you only need to know which model-backed metrics are available and what constructor arguments they accept.

```python
import inspect
from torchmetrics.text import BERTScore
from torchmetrics.multimodal import CLIPScore, CLIPImageQualityAssessment
from torchmetrics.image import FrechetInceptionDistance, LearnedPerceptualImagePatchSimilarity

print(inspect.signature(BERTScore.__init__))
print(inspect.signature(CLIPScore.__init__))
print(inspect.signature(CLIPImageQualityAssessment.__init__))
print(inspect.signature(FrechetInceptionDistance.__init__))
print(inspect.signature(LearnedPerceptualImagePatchSimilarity.__init__))
```

Practical notes:

- This route avoids downloads and is safe in offline or cache-empty environments.
- Use it when you only need API discovery, not actual score computation.

## 2) BERTScore planning

```python
from torchmetrics.text import BERTScore

metric = BERTScore(model_name_or_path="roberta-base", rescale_with_baseline=False, batch_size=64)
```

Practical notes:

- `model_name_or_path` can point to a Hugging Face model id or a local checkpoint path.
- If you already have your own tokenizer or model, supply them explicitly.
- Keep `device` and `batch_size` realistic for the available memory.

## 3) CLIPScore and CLIP-IQA planning

```python
from torchmetrics.multimodal import CLIPScore, CLIPImageQualityAssessment

clip_score = CLIPScore(model_name_or_path="openai/clip-vit-large-patch14")
clip_iqa = CLIPImageQualityAssessment(model_name_or_path="clip_iqa", data_range=1.0)
```

Practical notes:

- These metrics are only useful when the image/text prompts or quality prompts match the intended evaluation protocol.
- Default model names may require pretrained asset downloads.

## 4) Image feature metrics planning

```python
from torchmetrics.image import FrechetInceptionDistance, KernelInceptionDistance, LearnedPerceptualImagePatchSimilarity

fid = FrechetInceptionDistance(feature=2048, reset_real_features=True, normalize=False)
kid = KernelInceptionDistance(feature=2048, normalize=False)
lpips = LearnedPerceptualImagePatchSimilarity(net_type="vgg", normalize=True)
```

Practical notes:

- FID/KID require real and fake image streams or batches.
- `reset_real_features=True` changes how the real-image cache behaves across runs.
- LPIPS and DISTS are perceptual similarity metrics, not generative quality scores.

## 5) Audio and video model-backed metrics planning

```python
from torchmetrics.audio import DeepNoiseSuppressionMeanOpinionScore, NonIntrusiveSpeechQualityAssessment
from torchmetrics.video import VideoMultiMethodAssessmentFusion

# Only plan these after checking their optional runtime assets.
```

Practical notes:

- DNSMOS and NISQA may need `librosa`, `onnxruntime`, and network-backed assets.
- VMAF depends on `vmaf_torch`; `features=True` is a useful no-download inspection mode.

## 6) Smoke script workflow

Run the bundled import check when you want to confirm the package exposes the expected classes without fetching pretrained assets.

```bash
python scripts/model_based_import_check.py
```

Use the script before you commit to a runtime plan that assumes cached weights or network access.
