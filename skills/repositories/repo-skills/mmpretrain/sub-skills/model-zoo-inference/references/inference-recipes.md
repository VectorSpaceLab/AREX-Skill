# MMPreTrain inference recipes

These recipes use only installed MMPreTrain public APIs. Replace model names, image paths, text prompts, checkpoint paths, and output directories with user-provided values.

## Safe model discovery

List local model-zoo entries without downloading checkpoints:

```python
from mmpretrain.apis import list_models, ImageClassificationInferencer

print(list_models('resnet18'))
print(list_models('blip', task='Image Caption'))
print(ImageClassificationInferencer.list_models('convnext'))
```

Shell helper:

```bash
python skills/disco/mmpretrain/sub-skills/model-zoo-inference/scripts/list_models.py --pattern resnet18
python skills/disco/mmpretrain/sub-skills/model-zoo-inference/scripts/list_models.py --task "Image Classification" --pattern eva --as-json
python skills/disco/mmpretrain/sub-skills/model-zoo-inference/scripts/list_models.py --inferencer caption
```

If discovery fails before any model list is returned, see `troubleshooting.md#missing-model-index-assets`.

## Choosing weights deliberately

MMPreTrain has two different defaults:

- `get_model(..., pretrained=False)` does not load weights.
- Task inferencers default to `pretrained=True`, so they may download default weights for a model-zoo name.

Use this decision table before running inference:

| User intent | Use |
| --- | --- |
| Inspect architecture or modify layers only | `pretrained=False` |
| Offline smoke test where prediction quality does not matter | `pretrained=False`, `device='cpu'` |
| Meaningful prediction with a local file | `pretrained='checkpoints/model.pth'` |
| Meaningful prediction and network is allowed | `pretrained=True` or a checkpoint URL |
| Mirror a known URL to local storage | `url_mapping=(r'https://download.example/.*/', 'checkpoints/')` |

## Image classification

No-download, random-weight construction for API smoke or shape/debug work:

```python
from mmpretrain.apis import ImageClassificationInferencer

inferencer = ImageClassificationInferencer(
    'resnet18_8xb32_in1k',
    pretrained=False,
    device='cpu',
)
results = inferencer('images/example.jpg', batch_size=1)
print(results[0]['pred_label'], results[0].get('pred_class'))
```

Meaningful classification with an explicit checkpoint:

```python
from mmpretrain.apis import ImageClassificationInferencer

inferencer = ImageClassificationInferencer(
    model='resnet18_8xb32_in1k',
    pretrained='checkpoints/resnet18.pth',
    device='cpu',
)
results = inferencer(
    ['images/a.jpg', 'images/b.jpg'],
    batch_size=2,
    show=False,
    show_dir='outputs/classification-vis',
)
for item in results:
    print(item['pred_label'], item['pred_score'], item.get('pred_class'))
```

Custom class names for display and `pred_class` mapping:

```python
classes = ['cat', 'dog', 'other']
inferencer = ImageClassificationInferencer(
    'custom_classifier',
    pretrained='checkpoints/custom.pth',
    device='cpu',
    classes=classes,
)
```

Shell helper that avoids downloads by default:

```bash
python skills/disco/mmpretrain/sub-skills/model-zoo-inference/scripts/classify_image.py \
  --image images/example.jpg \
  --model resnet18_8xb32_in1k \
  --device cpu \
  --topk 5
```

For meaningful predictions with the helper, pass either `--checkpoint checkpoints/model.pth` or `--use-default-checkpoint`.

## `inference_model` quick shortcut

Use `inference_model` only when a single quick result is enough:

```python
from mmpretrain.apis import inference_model

result = inference_model('resnet18_8xb32_in1k', 'images/example.jpg', pretrained=False)
print(result)
```

For repeated calls, batching, visualization, retrieval prototypes, or `return_datasamples=True`, instantiate the relevant inferencer instead.

## No-download model surgery and feature extraction

Use `get_model` when the user wants architecture changes before inference or feature extraction. This pattern avoids checkpoint download and is suitable for synthetic tests, model surgery, and shape inspection:

```python
from mmpretrain.apis import FeatureExtractor, get_model

model = get_model(
    'resnet18_8xb32_in1k',
    pretrained=False,
    device='cpu',
    head=None,
    neck=None,
    backbone=dict(out_indices=(1, 2, 3)),
)
extractor = FeatureExtractor(model)
features = extractor('images/example.jpg', batch_size=1, stage='backbone')[0]
for i, feat in enumerate(features):
    print(i, tuple(feat.shape))
```

Notes:

- Features from `pretrained=False` models are random and should not be used for quality claims.
- `stage` and returned shapes depend on the model's `extract_feat` implementation.
- If you remove the head or neck, prefer `FeatureExtractor` or direct `model.extract_feat` over classification postprocessing.

## Retrieval prototypes, caches, and top-k

Image-to-image retrieval:

```python
from mmpretrain.apis import ImageRetrievalInferencer

inferencer = ImageRetrievalInferencer(
    model='resnet50-arcface_inshop',
    prototype='prototype_images/',
    prototype_cache='cache/image_retrieval_prototype.pth',
    prepare_batch_size=8,
    pretrained='checkpoints/retrieval_model.pth',
    device='cpu',
)
matches = inferencer('queries/query.jpg', topk=5, show_dir='outputs/retrieval-vis')[0]
for match in matches:
    print(match['sample_idx'], float(match['match_score']), match['sample'])
```

Text-to-image retrieval:

```python
from mmpretrain.apis import TextToImageRetrievalInferencer

inferencer = TextToImageRetrievalInferencer(
    model='blip-base_3rdparty_retrieval',
    prototype=['prototype_images/a.jpg', 'prototype_images/b.jpg'],
    prototype_cache='cache/t2i_prototype.pth',
    fast_match=True,
    pretrained='checkpoints/blip_retrieval.pth',
    device='cpu',
)
matches = inferencer(['a dog on grass', 'a red bird'], batch_size=2, topk=3)
```

Image-to-text retrieval:

```python
from mmpretrain.apis import ImageToTextRetrievalInferencer

texts = ['a cat on a blanket', 'a dog in a park', 'a bird in a tree']
inferencer = ImageToTextRetrievalInferencer(
    model='blip-base_3rdparty_retrieval',
    prototype=texts,
    prototype_cache='cache/i2t_prototype.pth',
    fast_match=True,
    pretrained='checkpoints/blip_retrieval.pth',
    device='cpu',
)
matches = inferencer('queries/bird.jpg', topk=2)[0]
```

Prototype/cache rules:

- `prototype_cache` is tied to the model architecture, checkpoint, preprocessing pipeline, prototype list/folder, and often `fast_match`; delete and rebuild it after any of those change.
- Keep `topk` less than or equal to the number of prototype samples.
- Use `prepare_batch_size` to control memory while building prototype features.
- Use `return_datasamples=True` when downstream code needs raw score tensors.

## Multimodal inferencers

These tasks often require optional dependencies such as tokenizer/model packages in addition to base MMPreTrain. If imports or model construction fail, check the optional-extra troubleshooting section.

Captioning:

```python
from mmpretrain.apis import ImageCaptionInferencer

inferencer = ImageCaptionInferencer(
    'blip-base_3rdparty_caption',
    pretrained='checkpoints/caption_model.pth',
    device='cpu',
)
print(inferencer('images/example.jpg')[0]['pred_caption'])
```

Visual question answering:

```python
from mmpretrain.apis import VisualQuestionAnsweringInferencer

inferencer = VisualQuestionAnsweringInferencer(
    'ofa-base_3rdparty-zeroshot_vqa',
    pretrained='checkpoints/vqa_model.pth',
    device='cpu',
)
answer = inferencer('images/example.jpg', 'What animal is shown?')[0]
print(answer['question'], answer['pred_answer'])
```

Visual grounding:

```python
from mmpretrain.apis import VisualGroundingInferencer

inferencer = VisualGroundingInferencer(
    'ofa-base_3rdparty_refcoco',
    pretrained='checkpoints/grounding_model.pth',
    device='cpu',
)
boxes = inferencer('images/example.jpg', 'the dog', show_dir='outputs/grounding-vis')[0]
print(boxes['pred_bboxes'])
```

Natural Language for Visual Reasoning:

```python
from mmpretrain.apis import NLVRInferencer

inferencer = NLVRInferencer(
    'nlvr_model_name',
    pretrained='checkpoints/nlvr_model.pth',
    device='cpu',
)
result = inferencer(('images/left.jpg', 'images/right.jpg', 'two dogs are present'))[0]
print(result['pred_label'], result['pred_score'])
```

## Batch, visualization, and output handling

- Use `batch_size` for repeated inference. For a directory input, the base inferencer can expand local directory files into a list.
- In headless sessions, keep `show=False` and set `show_dir='outputs/vis'` when visualization files are needed.
- Dictionary outputs may contain NumPy arrays or tensors. Convert them before JSON serialization, or remove verbose fields such as `pred_scores`.
- Use `return_datasamples=True` to preserve `DataSample` objects rather than simplified dictionaries.

## Device and offload choices

CPU default:

```python
inferencer = ImageClassificationInferencer('resnet18_8xb32_in1k', pretrained=False, device='cpu')
```

CUDA only when the active install supports it:

```python
inferencer = ImageClassificationInferencer('resnet18_8xb32_in1k', pretrained='checkpoints/model.pth', device='cuda:0')
```

Large-model offload pattern:

```python
inferencer = ImageCaptionInferencer(
    'large_caption_model',
    pretrained='checkpoints/large_caption_model.pth',
    device_map='auto',
    offload_folder='offload-cache',
)
```

If `device_map` fails, treat it as an optional dependency/offload problem rather than a model-name problem.
