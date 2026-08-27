# MMPreTrain model-zoo and inference API reference

This reference summarizes the installed MMPreTrain public inference surface for future agents. It is self-contained; do not rely on repository source files or external documentation during operation.

## Imports

```python
from mmpretrain.apis import (
    ModelHub,
    list_models,
    get_model,
    inference_model,
    ImageClassificationInferencer,
    ImageRetrievalInferencer,
    FeatureExtractor,
    ImageCaptionInferencer,
    VisualQuestionAnsweringInferencer,
    VisualGroundingInferencer,
    TextToImageRetrievalInferencer,
    ImageToTextRetrievalInferencer,
    NLVRInferencer,
)
```

The package also re-exports these APIs from `mmpretrain` in typical installs.

## Model discovery

### `list_models`

Verified signature:

```python
list_models(pattern=None, exclude_patterns=None, task=None) -> list[str]
```

- `pattern`: wildcard pattern matched against model names. The implementation appends a trailing `*`, so `pattern='resnet18'` finds names beginning with `resnet18`, and wildcard patterns such as `resnet*in1k` are also useful.
- `exclude_patterns`: list of wildcard patterns to subtract from the matched names. Each pattern is also treated as a prefix-style wildcard by appending `*`.
- `task`: exact model-index task string, for example `Image Classification`, `Image Retrieval`, `Image Caption`, `Visual Question Answering`, `Visual Grounding`, `Text-To-Image Retrieval`, `Image-To-Text Retrieval`, `NLVR`, or `null` for entries without result metadata.
- Return value: sorted list of lower-case model names.
- Network behavior: local metadata only; it should not download checkpoints.

Examples:

```python
from mmpretrain.apis import list_models

all_resnet18 = list_models('resnet18')
classification_eva = list_models('eva', task='Image Classification')
non_pretrained_swin = list_models('swin', exclude_patterns=['swinv2', '*-pre'])
```

### Inferencer-specific model lists

Each inferencer has `ClassName.list_models(pattern=None)` and filters by its task:

| Inferencer | Task filter |
| --- | --- |
| `ImageClassificationInferencer` | `Image Classification` |
| `ImageRetrievalInferencer` | `Image Retrieval` |
| `ImageCaptionInferencer` | `Image Caption` |
| `VisualQuestionAnsweringInferencer` | `Visual Question Answering` |
| `VisualGroundingInferencer` | `Visual Grounding` |
| `TextToImageRetrievalInferencer` | `Text-To-Image Retrieval` |
| `ImageToTextRetrievalInferencer` | `Image-To-Text Retrieval` |
| `NLVRInferencer` | `NLVR` |
| `FeatureExtractor` | no task filter; equivalent to model-zoo `list_models(pattern)` |

Use the bundled helper for shell discovery:

```bash
python skills/disco/mmpretrain/sub-skills/model-zoo-inference/scripts/list_models.py --pattern resnet18
python skills/disco/mmpretrain/sub-skills/model-zoo-inference/scripts/list_models.py --inferencer classification --limit 10
```

## `ModelHub`

`ModelHub` hosts parsed model-index metadata.

Common methods:

- `ModelHub.get(model_name)`: returns a copied model metadata object for `model_name`, lazily loading the config. Raises `ValueError` when the name is unknown.
- `ModelHub.has(model_name)`: checks the currently registered metadata dictionary. If the packaged model index has not been registered yet, call `list_models()` first or use `ModelHub.get()` and handle `ValueError`.
- `ModelHub.register_model_index(model_index_path, config_prefix=None)`: advanced use for registering an additional compatible model-index file. Only use when the user intentionally provides an external model index.

`ModelHub.get()` lower-cases the lookup key, but names should still be copied from `list_models()` to avoid spelling and suffix mistakes.

## `get_model` and checkpoint selection

Verified signature:

```python
get_model(
    model,
    pretrained=False,
    device=None,
    device_map=None,
    offload_folder=None,
    url_mapping=None,
    **kwargs,
)
```

Accepted `model` values:

- model-zoo name, such as `resnet18_8xb32_in1k`;
- config file path ending in `.py`;
- `mmengine.Config` object.

Checkpoint behavior:

| `pretrained` value | Behavior |
| --- | --- |
| `False` | Do not load weights. This is the safest offline/default construction mode. |
| `True` | If a model-zoo entry has default weights, load them; this may download. If no default weights exist, no weights are loaded and a warning is emitted. |
| string | Treat as a local checkpoint path or URL and load it with CPU map-location before moving/dispatching the model. |

Other construction controls:

- `device='cpu'`, `device='cuda'`, or `device='cuda:0'` moves the model after loading. Use only devices supported by the active PyTorch install.
- `device_map` dispatches submodules according to a map such as `'auto'` or a dict. If any module maps to disk, set a writable `offload_folder`. This path is for large-model/offload workflows and can require optional dependencies.
- `url_mapping=(pattern, replacement)` rewrites a checkpoint URL before loading. Use it to redirect known URL prefixes to a local mirror/cache.
- `**kwargs` merges into `config.model`. This is the mechanism for architecture changes such as `head=None`, `neck=None`, or `backbone=dict(out_indices=(0, 1, 2, 3))`.

The returned object is an evaluated MMEngine model with `_config`, `_metainfo`, and `_dataset_meta` attached when available.

No-download construction examples:

```python
from mmpretrain.apis import get_model

model = get_model('resnet18_8xb32_in1k', pretrained=False, device='cpu')
headless = get_model(
    'resnet18_8xb32_in1k',
    pretrained=False,
    device='cpu',
    head=None,
    neck=None,
    backbone=dict(out_indices=(1, 2, 3)),
)
```

## `inference_model` shortcut

Signature:

```python
inference_model(model, *args, **kwargs)
```

Use it only for a quick single-call demo. It chooses an inferencer from model-index task metadata and returns the first result dictionary, not a list. If a model advertises multiple tasks, it warns and chooses one. If no task maps to an inferencer, it raises `NotImplementedError`.

For repeated inference, batching, retrieval prototypes, visualization, `return_datasamples`, or checkpoint/device/offload control, instantiate the task inferencer directly.

## Shared inferencer behavior

All task inferencers accept a model-zoo name, config path, `Config`, or already built `BaseModel`. If the `model` argument is already a model object and `pretrained` is a string, the checkpoint is loaded into that object. Otherwise the inferencer calls `get_model`.

Most inferencers have:

- constructor default `pretrained=True`, which can trigger a default checkpoint download;
- `device`, and for most multimodal/feature classes `device_map` and `offload_folder`;
- `__call__(..., return_datasamples=False, batch_size=1, **kwargs)`;
- string path, URL, NumPy array, list, and in some cases directory inputs;
- `show=False` default and optional `show_dir` visualization output.

`return_datasamples=True` returns MMPreTrain `DataSample` objects instead of simplified dictionaries. This is useful when tensors, raw predicted fields, or downstream custom postprocessing are needed.

## Inferencer signatures and returns

### Image classification

Constructor:

```python
ImageClassificationInferencer(model, pretrained=True, device=None, classes=None, **kwargs)
```

Call:

```python
inferencer(inputs, return_datasamples=False, batch_size=1, **kwargs)
```

Inputs are image paths, image URLs, NumPy arrays, lists, or a directory path expanded to files. Visualization kwargs include `resize`, `rescale_factor`, `draw_score`, `show`, `show_dir`, and `wait_time`.

Dictionary return per image:

```python
{
    'pred_scores': <numpy array>,
    'pred_label': <int>,
    'pred_score': <float>,
    'pred_class': <class name if classes metadata is available>,
}
```

Pass `classes=[...]` to override or supply class names for display and `pred_class` mapping.

### Image-to-image retrieval

Constructor:

```python
ImageRetrievalInferencer(
    model,
    prototype,
    prototype_cache=None,
    prepare_batch_size=8,
    pretrained=True,
    device=None,
    **kwargs,
)
```

`prototype` can be an image directory, list of image paths, dataset config dict, `BaseDataset`, or `DataLoader`. If `prototype_cache` exists, cached prototype features are loaded. If it does not exist, features are computed and saved there. Call with `topk=<int>` to choose match count.

Dictionary return per query is a list of matches:

```python
[
    {
        'match_score': <tensor>,
        'sample_idx': <int>,
        'sample': <prototype sample metadata>,
    },
    ...
]
```

Visualization kwargs include `topk`, `resize`, `draw_score`, `show`, `show_dir`, and `wait_time`.

### Feature extraction

Constructor:

```python
FeatureExtractor(model, pretrained=True, device=None, device_map=None, offload_folder=None, **kwargs)
```

Call:

```python
extractor(inputs, batch_size=1, **extract_feat_kwargs)
```

`FeatureExtractor` returns a list of per-image tensors or nested tensor sequences. Extra kwargs are passed to the model's `extract_feat`, such as `stage='backbone'` for models that support stage selection. It does not visualize or postprocess.

### Image captioning

Constructor:

```python
ImageCaptionInferencer(model, pretrained=True, device=None, device_map=None, offload_folder=None, **kwargs)
```

Call:

```python
inferencer(images, return_datasamples=False, batch_size=1, **kwargs)
```

Dictionary return per image:

```python
{'pred_caption': <str>}
```

Visualization kwargs include `resize`, `show`, `show_dir`, and `wait_time`.

### Visual question answering

Constructor:

```python
VisualQuestionAnsweringInferencer(model, pretrained=True, device=None, device_map=None, offload_folder=None, **kwargs)
```

Call:

```python
inferencer(images, questions, return_datasamples=False, batch_size=1, objects=None, **kwargs)
```

For a single image, `questions` is a string. For a list of images, pass a list of question strings. Some algorithms accept `objects`, a list of object descriptions per image.

Dictionary return per image:

```python
{'question': <str>, 'pred_answer': <str>}
```

### Visual grounding

Constructor:

```python
VisualGroundingInferencer(model, pretrained=True, device=None, device_map=None, offload_folder=None, **kwargs)
```

Call:

```python
inferencer(images, texts, return_datasamples=False, batch_size=1, **kwargs)
```

Dictionary return per image/text pair:

```python
{'pred_bboxes': <tensor>}
```

Visualization kwargs include `resize`, `show`, `show_dir`, `wait_time`, `line_width`, and `bbox_color`.

### Text-to-image retrieval

Constructor:

```python
TextToImageRetrievalInferencer(
    model,
    prototype,
    prototype_cache=None,
    fast_match=True,
    prepare_batch_size=8,
    pretrained=True,
    device=None,
    **kwargs,
)
```

`prototype` is an image directory, list of image paths, dataset config dict, `BaseDataset`, or `DataLoader`. Call inputs are text strings or lists of strings. Return format matches image retrieval: each query yields a list of image matches. Visualization kwargs include `topk`, `figsize`, `draw_score`, `show`, `show_dir`, and `wait_time`.

### Image-to-text retrieval

Constructor:

```python
ImageToTextRetrievalInferencer(
    model,
    prototype,
    prototype_cache=None,
    fast_match=True,
    prepare_batch_size=8,
    pretrained=True,
    device=None,
    **kwargs,
)
```

`prototype` is a text-file path containing one string per line, or a Python list of strings. Call inputs are images. Return per query:

```python
[
    {
        'match_score': <tensor>,
        'sample_idx': <tensor/int-like index>,
        'text': <matched text>,
    },
    ...
]
```

Visualization kwargs include `topk`, `resize`, `draw_score`, `show`, `show_dir`, and `wait_time`.

### NLVR

Constructor:

```python
NLVRInferencer(model, pretrained=True, device=None, device_map=None, offload_folder=None, **kwargs)
```

Call:

```python
inferencer(inputs, return_datasamples=False, batch_size=1, **kwargs)
```

Each input is `(left_image, right_image, text)`, or a list of those tuples. Dictionary return per tuple:

```python
{
    'pred_scores': <numpy array>,
    'pred_label': <int>,
    'pred_score': <float>,
}
```

Visualization kwargs include `resize`, `draw_score`, `show`, `show_dir`, and `wait_time`.
