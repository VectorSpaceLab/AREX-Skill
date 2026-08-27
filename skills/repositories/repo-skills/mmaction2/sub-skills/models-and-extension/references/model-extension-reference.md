# MMAction2 model and extension reference

This reference is self-contained operating guidance for model-family selection, registry behavior, and extension work in MMAction2 1.x.

## Mental model

MMAction2 is organized around MMEngine registries. A config or Python snippet usually describes a component with a `dict(type='ClassName', ...)`; the active registry and default scope resolve that string to a class. The most important scope for core MMAction2 is `mmaction`.

Typical standalone setup:

```python
from mmaction.utils import register_all_modules
from mmaction.registry import MODELS, DATASETS, TRANSFORMS, METRICS

register_all_modules(init_default_scope=True)
model = MODELS.build(dict(type='Recognizer3D', backbone=..., cls_head=...))
```

When a script already has an MMEngine runner or config, keep `default_scope='mmaction'` in the config unless the task intentionally composes another OpenMMLab package.

## Core registry map

| Registry | Typical contents | Use it for |
| --- | --- | --- |
| `MODELS` | recognizers, backbones, heads, losses, data preprocessors, necks, localizers, similarity modules, batch augmentations | Model/component construction and customization |
| `DATASETS` | action/video/rawframe/pose/audio/AVA/retrieval/text datasets | Dataset class selection; routine annotation schemas route to data-and-configs |
| `TRANSFORMS` | video loading, sampling, decoding, resizing/cropping/flipping, pose transforms, formatting, text tokenization, wrappers | Pipeline component selection; routine pipeline editing routes to data-and-configs |
| `METRICS` | accuracy, confusion matrix, AVA, ANet, retrieval, multimodal/VQA, video grounding, MultiSports metrics | Metric class selection; command/result execution routes to training-and-evaluation |
| `INFERENCERS` | action recognition inferencers | Inference route only; see inference-and-demos for actual use |
| `HOOKS`, `LOOPS`, `OPTIMIZERS`, `OPTIM_WRAPPERS`, `PARAM_SCHEDULERS` | training runtime extension points | Only model-extension should explain registration; training usage routes out |
| `VISUALIZERS`, `VISBACKENDS` | action visualizer and video backends | Usually inference/visualization route |
| `TOKENIZER` | multimodal tokenizer surface | Retrieval/VQA/multimodal extension |

The registry probe script bundled with this sub-skill summarizes currently importable registry names and counts without downloading weights or launching jobs.

## Model zoo and family categories

MMAction2's model index/metafile surface groups models by task rather than by one universal architecture. Use the task first, then choose the family whose input modality and head shape match the user's data.

| Task surface | Representative families/classes | Input/output assumptions |
| --- | --- | --- |
| RGB recognition, 2D/2D+temporal | `Recognizer2D`, TSN, TSM, TRN, TIN, TANet, C2D, MobileNet/ResNet backbones, OmniSource variants | Inputs are usually `N x views x C x H x W` after `FormatShape`/preprocessing. Heads such as `TSNHead` often receive flattened views and use `num_segs` consensus. |
| RGB recognition, 3D/transformer | `Recognizer3D`, C3D, I3D, SlowOnly, SlowFast, R(2+1)D, CSN, X3D, MViT, Swin, TimeSformer, UniFormer/UniFormerV2, VideoMAE/VideoMAEv2 | Inputs are usually `N x views x C x T x H x W`; 3D heads pool `C x T x H x W` features. `max_testing_views` can reduce memory for multi-view testing. |
| Skeleton/action from pose | `RecognizerGCN`, AAGCN, STGCN/STGCN++, PoseC3D, `RGBPoseConv3D`, `GCNHead`, `RGBPoseHead` | GCN inputs are usually `B x num_clips x num_person x T x V x C`; PoseC3D uses generated pose heatmaps as 3D volumes. Keypoint layout must match graph/pipeline assumptions. |
| Audio recognition | `RecognizerAudio`, `ResNetAudio`, `TSNAudioHead`, `AudioDataset`, audio formatting | Requires audio feature extraction/decoding dependencies for real data. Head `num_classes` still follows the label space. |
| Spatio-temporal action detection | AVA/MultiSports-style `FastRCNN` configs with MMAction2 ROI heads and bbox heads registered into MMDetection registries | Requires MMDetection for ROI/detection components. `bbox_head.num_classes` is label-space specific; AVA-style configs commonly include background/attribute conventions that differ from video-level recognition. |
| Temporal action localization | `BMN`, `BSN` (`TEM`, `PEM`), `DRN`, `TCANet`, `ANetMetric` | Uses proposal/localization data, not video-level class labels. Do not force recognition heads onto localization configs. |
| Video-text retrieval and multimodal/VQA | `CLIPSimilarity`, CLIP4Clip, VindLU retrieval/MC/VQA, MSRVTT datasets, `VideoTextDataset`, `RetrievalMetric`, `RetrievalRecall`, `VQAAcc` | Optional multimodal dependencies are required. Treat tokenizer/text transforms as part of the model surface, not a plain RGB recognizer. |

Observed model-index family groups include recognition (`c2d`, `c3d`, `csn`, `i3d`, `mvit`, `omnisource`, `r2plus1d`, `slowfast`, `slowonly`, `swin`, `tanet`, `timesformer`, `tin`, `tpn`, `trn`, `tsm`, `tsn`, `uniformer`, `uniformerv2`, `videomae`, `videomaev2`, `x3d`), detection (`acrn`, `lfb`, `slowfast`, `slowonly`, `videomae`), localization (`bmn`, `bsn`, `drn`, `tcanet`), skeleton (`2s-agcn`, `posec3d`, `stgcn`, `stgcnpp`), audio (`resnet`), retrieval (`clip4clip`), and multimodal (`vindlu`).

## Representative registered components

Use these names to reason about component compatibility; the probe script can confirm what is importable in the active environment.

### Recognizers and task models

- Recognition: `Recognizer2D`, `Recognizer3D`, `MMRecognizer3D`, `RecognizerAudio`, `RecognizerGCN`, `RecognizerOmni`.
- Localization: `BMN`, `TEM`, `PEM`, `DRN`, `TCANet`.
- Multimodal/retrieval: `CLIPSimilarity`, `VindLURetrieval`, `VindLURetrievalMC`, `VindLUVQA` when multimodal extras are installed; placeholders raise an informative extra-install error otherwise.

### Backbones

`AAGCN`, `C2D`, `C3D`, `MobileNetV2`, `MobileNetV2TSM`, `MobileOneTSM`, `MViT`, `ResNet`, `ResNet2Plus1d`, `ResNet3d`, `ResNet3dLayer`, `ResNet3dCSN`, `ResNet3dSlowFast`, `ResNet3dSlowOnly`, `ResNetAudio`, `OmniResNet`, `ResNetTIN`, `ResNetTSM`, `RGBPoseConv3D`, `STGCN`, `SwinTransformer3D`, `TANet`, `TimeSformer`, `UniFormer`, `UniFormerV2`, `VisionTransformer`, `X3D`, plus project-defined backbones when imported and registered.

### Heads and necks

- Heads: `TSNHead`, `TSMHead`, `TRNHead`, `I3DHead`, `SlowFastHead`, `X3DHead`, `MViTHead`, `TimeSformerHead`, `UniFormerHead`, `TPNHead`, `GCNHead`, `RGBPoseHead`, `TSNAudioHead`, `FeatureHead`, `OmniHead`.
- Neck: `TPN`.
- Detection ROI components are exposed through MMDetection registries when MMDetection is installed: AVA ROI head, AVA bbox head, 3D ROI extractor, ACRN/FBO/LFB shared heads.

### Losses, preprocessors, and metrics

- Losses: `CrossEntropyLoss`, `BCELossWithLogits`, `CBFocalLoss`, `NLLLoss`, `HVULoss`, `SSNLoss`, `BMNLoss`, `BinaryLogisticRegressionLoss`.
- Data preprocessors: `ActionDataPreprocessor`, `MultiModalDataPreprocessor`.
- Batch blending/augmentation: `MixupBlending`, `CutmixBlending`, `RandomBatchAugment`.
- Metrics: `AccMetric`, `ConfusionMatrix`, `AVAMetric`, `ANetMetric`, `RetrievalMetric`, `RetrievalRecall`, `VQAAcc`, `ReportVQA`, `VQAMCACC`, `MultiSportsMetric`, `RecallatTopK`.

### Datasets and transforms relevant to extension

- Datasets: `VideoDataset`, `RawframeDataset`, `PoseDataset`, `AudioDataset`, `AVADataset`, `AVAKineticsDataset`, `ActivityNetDataset`, `CharadesSTADataset`, `VideoTextDataset`, MSRVTT VQA/retrieval variants, `RepeatAugDataset`.
- Loading/sampling transforms include `DecordInit`, `DecordDecode`, `RawFrameDecode`, `SampleFrames`, `UniformSample`, `DenseSampleFrames`, `SampleAVAFrames`, audio/feature/pose loaders.
- Processing/formatting transforms include `Resize`, `RandomResizedCrop`, `Flip`, `CenterCrop`, `ThreeCrop`, `TenCrop`, `FormatShape`, `FormatAudioShape`, `FormatGCNInput`, `PackActionInputs`, pose transforms (`DecompressPose`, `GeneratePoseTarget`, `PreNormalize2D/3D`, `JointToBone`, `GenSkeFeat`) and text tokenization (`CLIPTokenize`).

## Default scope and imports

### Core package modules

For scripts and notebooks, call:

```python
from mmaction.utils import register_all_modules
register_all_modules(init_default_scope=True)
```

This imports MMAction2 datasets, engine components, evaluation, models, structures, and visualization modules and sets `mmaction` as the active MMEngine default scope. If a caller is composing registries from another OpenMMLab package, use `init_default_scope=False` only after confirming that each config item has an explicit scope or an imported class.

### Custom Python modules

A custom component must satisfy both requirements:

1. Python can import the module.
2. The component class is registered into the correct registry.

Minimal custom backbone pattern:

```python
from mmaction.models import ResNet
from mmaction.registry import MODELS

@MODELS.register_module()
class MyBackbone(ResNet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
```

Config-side pattern:

```python
custom_imports = dict(imports=['my_project.models.my_backbone'], allow_failed_imports=False)
default_scope = 'mmaction'
model = dict(backbone=dict(type='MyBackbone', depth=50))
```

If the custom module lives in a standalone project, install that project as a Python package or add its parent to `PYTHONPATH` for the current session. Do not rely on implicit current-directory imports.

## Custom dataset and transform patterns

Detailed annotation schemas and pipeline editing belong to the data-and-configs sub-skill. For registry extension, the minimum patterns are:

```python
from mmengine.dataset import BaseDataset
from mmaction.registry import DATASETS

@DATASETS.register_module()
class MyActionDataset(BaseDataset):
    def load_data_list(self):
        return [dict(filename='relative_or_absolute_video.mp4', label=0)]
```

```python
from mmcv.transforms import BaseTransform
from mmaction.registry import TRANSFORMS

@TRANSFORMS.register_module()
class MyTransform(BaseTransform):
    def transform(self, results):
        results['my_key'] = True
        return results
```

The pipeline must provide keys that downstream transforms and `PackActionInputs` expect. For example, video recognition usually needs a filename or decoded frames plus a `label`; pose workflows need keypoints/score/shape metadata; AVA detection uses timestamps, proposals, boxes, and labels.

## Project-style extension pattern

MMAction2 supports project-style extensions outside the core package. Treat them as less stable than core components and require explicit imports. A robust project pattern is:

- Put custom modules in an importable package such as `my_project.models`.
- Register model classes with `@MODELS.register_module()`.
- Add `custom_imports = dict(imports=['my_project.models'], allow_failed_imports=False)` to the config.
- Override only the component fields that change, for example `model.backbone.type` and `model.cls_head.in_channels`.
- Keep result tables, citations, conversion notes, and limitations with the project, but do not assume project code is part of MMAction2 core.

## Class-count and tensor shape cautions

### `num_classes`

- For video-level recognition heads, `cls_head.num_classes` must match the dataset label space. A two-class custom dataset needs `num_classes=2`, not the original Kinetics value.
- `AccMetric` supports top-k and mean-class accuracy. If `topk=(1, 5)` and `num_classes < 5`, adjust top-k to a valid value.
- Multi-label or HVU-style tasks may use soft/multi-hot labels with losses such as BCE/focal/HVU; do not treat them as ordinary integer class labels.
- AVA/spatio-temporal detection label spaces often differ from video-level recognition. A bbox head class count cannot be copied blindly from a recognition head.

### `in_channels`

- `cls_head.in_channels` must equal the feature channels emitted by the backbone/neck. ResNet-50 2D heads commonly use 2048, but transformer, SlowFast, TPN, RGB+pose, and project backbones can differ.
- `RGBPoseHead` expects a tuple of channel counts, one for RGB and one for pose.
- Detection heads can concatenate context, long-term feature-bank, or pathway features; their `in_channels` may be larger than the plain backbone output.

### Input format and recognizer family

- `Recognizer2D` flattens `N x num_views x C x H x W` into `N*num_views x C x H x W`, then passes `num_segs` to heads such as `TSNHead`.
- `Recognizer3D` flattens `N x num_views x C x T x H x W` into `N*num_views x C x T x H x W`.
- `RecognizerGCN` expects skeleton tensors shaped like `B x num_clips x num_person x T x V x C`; `GCNHead` pools features shaped like `N x M x C x T x V`.
- `ActionDataPreprocessor` normalizes as `NCHW`, `NCTHW`, or `MIX2d3d`; choose the format that matches `FormatShape`.
- `average_clips` accepts `score`, `prob`, or `None`. Invalid values raise a clear error; `None` preserves per-clip outputs and changes downstream shape expectations.
