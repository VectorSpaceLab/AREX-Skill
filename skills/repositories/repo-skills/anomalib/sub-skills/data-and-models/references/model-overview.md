# Model selection and registry

This reference focuses on the model-side choices that are most relevant to data/layout questions: how to list and instantiate models, which constructor knobs matter, and how to spot backbone/layer mismatches before they become runtime failures.

## 1) Registry and lookup

### Public helpers

- `list_models(case="snake" | "pascal" | "title")`
- `get_model(model, *args, **kwdargs)`
- `get_datamodule(config)` lives on the data side but is part of the same config flow

### `get_model()` accepted inputs

`get_model()` accepts:

- a model name string
- a dict with `class_path` and optional `init_args`
- an OmegaConf `DictConfig`
- a `jsonargparse.Namespace`

Allowed import roots are restricted to:

- `anomalib.models`
- `anomalib.models.image`
- `anomalib.models.video`
- `anomalib.models.components`

Unknown names raise `UnknownModelError`.

### Lookup guidance

- Prefer the class name when you already know it: `get_model("Padim")`
- Prefer snake-case when you want a short alias: `get_model("patchcore")`
- For fully qualified configs, keep the path inside the whitelisted anomalib modules
- If a lookup fails, verify case, spelling, and whether the class actually lives under a whitelisted module

### `list_models()` caveat

The `snake` form is mechanically derived from the class name, so acronym-heavy models may produce awkward spellings. Use `pascal` when you want a clean registry snapshot, and use the bundled script if you want the current repo build to print the list for you.

## 2) Verified model constructors

These are the constructor signatures and selection heuristics most likely to matter in practice.

| Model | Choose it when | Key knobs | Practical notes |
| --- | --- | --- | --- |
| `Padim` | You want a simple image baseline with multivariate Gaussian modeling. | `backbone`, `layers`, `pre_trained`, `n_features` | Default backbone is `resnet18`; default layers are `layer1/2/3`. If the backbone is not one of the built-in defaults, set `n_features` explicitly. |
| `Patchcore` | You want a strong image memory-bank baseline with k-center coreset sampling. | `backbone`, `layers`, `pre_trained`, `coreset_sampling_ratio`, `num_neighbors`, `precision` | Default backbone is `wide_resnet50_2`. Layer names must match the backbone's actual timm feature-map names. `precision` accepts `float32` or `float16`. |
| `EfficientAd` | You want a fast image model with student-teacher + autoencoder training. | `imagenet_dir`, `teacher_out_channels`, `model_size`, `lr`, `weight_decay`, `padding`, `pad_maps` | The training path prepares ImageNette and pretrained teacher weights. Training requires `train_batch_size == 1`, and the preprocessor must not include `Normalize`. |
| `AiVad` | You need video anomaly detection on clip tensors. | Region, velocity, pose, and deep-feature knobs | Works with video datamodules such as `Avenue`. No standard image preprocessor is needed; the model configures an empty one by default. |
| `Fuvas` | You need video anomaly segmentation from pretrained 3D backbones. | `backbone`, `layer`, `pre_trained`, `spatial_pool`, `pooling_kernel_size`, `pca_level` | Accepts backbones such as `x3d_s` and `swin3d_b`. Layer names must match the chosen backbone's extractor nodes. |

## 3) Constructor snapshots

```python
Padim(backbone="resnet18", layers=["layer1", "layer2", "layer3"], pre_trained=True, n_features=None, ...)
Patchcore(backbone="wide_resnet50_2", layers=("layer2", "layer3"), pre_trained=True, coreset_sampling_ratio=0.1, num_neighbors=9, precision="float32", ...)
EfficientAd(imagenet_dir="./datasets/imagenette", teacher_out_channels=384, model_size="small", lr=1e-4, weight_decay=1e-5, padding=False, pad_maps=True, ...)
AiVad(box_score_thresh=0.7, persons_only=False, min_bbox_area=100, max_bbox_overlap=0.65, enable_foreground_detections=True, foreground_kernel_size=3, foreground_binary_threshold=18, n_velocity_bins=1, use_velocity_features=True, use_pose_features=True, use_deep_features=True, n_components_velocity=2, n_neighbors_pose=1, n_neighbors_deep=1, ...)
Fuvas(backbone="x3d_s", layer="blocks.4", pre_trained=True, spatial_pool=True, pooling_kernel_size=1, pca_level=0.98, ...)
```

## 4) Feature extraction guidance

### When to use `TimmFeatureExtractor`

Use the timm-based feature extractor when the model needs intermediate backbone features from a CNN or transformer.

Typical cases:

- `Padim`
- `Patchcore`
- `Dfkde`
- `Dfm`
- `Fastflow`
- many other image models that build on timm backbones

### Backbone / layer alignment rules

- For CNN backbones, layer names must match actual module names such as `layer1`, `layer2`, `layer3`, or `blocks.4.1`
- For transformer backbones in `NLC` mode, layer names must look like `blocks.<index>`
- Missing layer names are warned about and removed; if all layers disappear, later feature extraction fails
- `dryrun_find_featuremap_dims()` is the safest way to check output channels and feature resolutions before you commit to a configuration

### Common backbone / layer pairs

| Backbone | Good starting layers |
| --- | --- |
| `resnet18` | `layer1`, `layer2`, `layer3` |
| `wide_resnet50_2` | `layer2`, `layer3` |
| `mobilenetv3_large_100` | `blocks.4.1`, `blocks.6.0` |
| `vit_base_patch14_reg4_dinov2` | `blocks.2`, `blocks.9` |

### Transformer mode reminders

- `TimmFeatureExtractor(..., output_fmt="NLC")` is the token-sequence path
- `return_class_token=True` prepends prefix tokens
- `norm=True` is often useful for transformer features that feed nearest-neighbor style models
- `dynamic_img_size=True` lets ViTs accept non-default input sizes more gracefully

## 5) Model-family selection hints

Use these broad cues when the user does not yet know which constructor to pick:

- `Padim` for a compact baseline and Gaussian modeling
- `Patchcore` when recall and memory-bank retrieval matter more than simplicity
- `EfficientAd` when training speed and deployment efficiency matter
- `AiVad` when the input is a clip, not a single image
- `Fuvas` when the input is a clip and the goal is segmentation from 3D backbones
- `AnomalyVFM`, `WinClip`, `VlmAd`, `AnomalyDINO`, `Dinomaly`, `GeneralAD`, or `SuperADD` when the user is specifically asking for foundation-model or transformer-heavy workflows

## 6) Registry snapshot for the current build

The current repository build exposes many more names through `list_models()`. Use the bundled script to print the exact current registry rather than relying on memory when the user wants the full list.

Good rule of thumb:

- If the user wants a quick answer, pick among the verified constructors above.
- If the user wants discovery, run `list_models()` or the bundled script.
- If the user wants a config file, prefer the exact constructor signature and defaults, then map those values into the YAML.
