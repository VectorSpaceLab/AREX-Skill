# API reference

This reference covers the public Torchreid APIs used for feature extraction, checkpoint loading, model discovery, complexity estimates, and result visualization.

## Model discovery and building

### `torchreid.models.show_avai_models()`

- Prints the exact registry keys accepted by `build_model()`.
- Use it when a prompt names a model family but not the precise key.

### `torchreid.models.build_model(name, num_classes, loss='softmax', pretrained=True, use_gpu=True)`

- Returns an `nn.Module`.
- `name` must be one of the registry keys below.
- `num_classes` is the training-ID count for the classifier head.
- `loss` is typically `softmax` or `triplet`.
- `pretrained=True` may trigger model-specific ImageNet weight loading and network access.
- Use `pretrained=False` for offline/no-download model construction.
- `use_gpu=True` only changes the model's internal device handling; it does not move input tensors for you.

### Registry keys

`show_avai_models()` prints the following exact keys:

| Family | Keys |
| --- | --- |
| ResNet / ResNeXt | `resnet18`, `resnet34`, `resnet50`, `resnet101`, `resnet152`, `resnext50_32x4d`, `resnext101_32x8d`, `resnet50_fc512` |
| SENet | `se_resnet50`, `se_resnet50_fc512`, `se_resnet101`, `se_resnext50_32x4d`, `se_resnext101_32x4d` |
| DenseNet | `densenet121`, `densenet169`, `densenet201`, `densenet161`, `densenet121_fc512` |
| Inception / Xception | `inceptionresnetv2`, `inceptionv4`, `xception` |
| IBN / AIN | `resnet50_ibn_a`, `resnet50_ibn_b`, `osnet_ibn_x1_0`, `osnet_ain_x1_0`, `osnet_ain_x0_75`, `osnet_ain_x0_5`, `osnet_ain_x0_25` |
| Lightweight / mobile | `nasnsetmobile`, `mobilenetv2_x1_0`, `mobilenetv2_x1_4`, `shufflenet`, `shufflenet_v2_x0_5`, `shufflenet_v2_x1_0`, `shufflenet_v2_x1_5`, `shufflenet_v2_x2_0`, `squeezenet1_0`, `squeezenet1_0_fc512`, `squeezenet1_1` |
| ReID-specific | `mudeep`, `resnet50mid`, `hacnn`, `pcb_p6`, `pcb_p4`, `mlfn`, `osnet_x1_0`, `osnet_x0_75`, `osnet_x0_5`, `osnet_x0_25` |

## Feature extractor

### `torchreid.utils.FeatureExtractor(...)`

Signature:

```python
FeatureExtractor(
    model_name='',
    model_path='',
    image_size=(256, 128),
    pixel_mean=[0.485, 0.456, 0.406],
    pixel_std=[0.229, 0.224, 0.225],
    pixel_norm=True,
    device='cuda',
    verbose=True
)
```

#### Construction behavior

- Builds the model with `build_model(model_name, num_classes=1, pretrained=..., use_gpu=...)`.
- If `model_path` exists, `FeatureExtractor` disables automatic pretrained loading and then calls `load_pretrained_weights()` on that local checkpoint.
- If `model_path` is missing or invalid, the underlying model constructor may try to fetch pretrained weights.
- When `verbose=True`, it prints estimated params and FLOPs via `compute_model_complexity()`.

#### Accepted input types

| Input | Shape / form | Handling |
| --- | --- | --- |
| `str` | Single image path | Open with PIL, resize, tensorize, normalize, batch to size 1. |
| `list[str]` | List of image paths | Process each image, stack into a batch. |
| `numpy.ndarray` | `H x W x C` | Converted to PIL, then resized, tensorized, normalized. |
| `list[numpy.ndarray]` | List of `H x W x C` arrays | Process each array, stack into a batch. |
| `torch.Tensor` | `C x H x W` or `B x C x H x W` | Moved to `device` as-is; no PIL preprocessing is applied. |

#### Return value

- Returns a `torch.Tensor` with shape `(B, D)`.
- `D` is architecture dependent.
- The helper is designed for inference/embedding extraction, not training.

#### Practical notes

- Use `device='cpu'` for safe smoke tests.
- If you already have a local checkpoint, pass its path explicitly.
- `device` may be `cpu`, `cuda`, or a specific CUDA device string such as `cuda:0`.
- If you want to avoid any network access, build the model with `pretrained=False` and/or supply a local `model_path`.

## Weight loading

### `torchreid.utils.load_pretrained_weights(model, weight_path)`

- Loads a checkpoint or a raw state dict.
- Strips a leading `module.` prefix automatically.
- Keeps unmatched layers unchanged.
- Ignores layers whose shapes do not match the target model.
- Warns when no layers match the checkpoint at all.

Use this when you need the lower-level model API instead of `FeatureExtractor`.

## Complexity estimate

### `torchreid.utils.compute_model_complexity(model, input_size, verbose=False, only_conv_linear=True)`

- Returns `(num_params, flops)`.
- `input_size` is a full tensor shape, e.g. `(1, 3, 256, 128)`.
- The FLOPs count is an estimate of the test-time graph, not real runtime.
- The classifier head is ignored when it is not part of the eval-time path.
- Set `only_conv_linear=False` if you want batch norm / activation costs too.

## Ranked-result visualization

### `torchreid.utils.visualize_ranked_results(distmat, dataset, data_type, width=128, height=256, save_dir='', topk=10)`

- `distmat` is a NumPy distance matrix of shape `(num_query, num_gallery)`.
- `dataset` is `(query, gallery)`.
- For image-ReID, query/gallery entries are tuples whose first three fields are `(img_path, pid, camid)`.
- For video-ReID, the first element may be a tracklet list or tuple of image paths.
- `data_type` is either `image` or `video`.
- Writes visualizations to `save_dir`.

## Representative model source behavior

- `torchreid.models.resnet.ResNet.forward(x)` returns embeddings in eval mode and logits in train mode.
- `torchreid.models.osnet.OSNet.forward(x, return_featuremaps=False)` supports a `return_featuremaps=True` branch that returns the last convolutional feature maps for activation-map visualization.
