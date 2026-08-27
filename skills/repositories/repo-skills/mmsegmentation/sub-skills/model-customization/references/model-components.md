# MMSegmentation Model Components

## Architecture Map

MMSegmentation models inherit MMEngine model conventions and organize semantic segmentation algorithms as segmentors made from reusable components.

- `EncoderDecoder` is the common segmentor. It builds `backbone`, optional `neck`, `decode_head`, optional `auxiliary_head`, `data_preprocessor`, `train_cfg`, and `test_cfg` through the `MODELS` registry.
- `CascadeEncoderDecoder` chains a list of decode heads. Earlier heads feed later heads, so `decode_head` must be a list with `num_stages` entries.
- `DepthEstimator` reuses the encoder-decoder pattern for depth maps and adds depth-specific prediction/loss expectations.
- `MultimodalEncoderDecoder` builds `image_encoder`, `text_encoder`, and `decode_head`; it is used by open-vocabulary style models where text embeddings participate in prediction.
- `SegTTAModel` wraps segmentation test-time augmentation behavior and belongs to model/runtime selection rather than custom component authoring.

The core model dataflow is:

1. `SegDataPreProcessor` collates, pads, converts channels, normalizes, and moves inputs/segmentation maps to the device.
2. The segmentor extracts features through the backbone and optional neck.
3. The decode head turns features into segmentation logits and computes decode loss or prediction post-processing.
4. Optional auxiliary heads add deep-supervision losses during training.
5. `forward(..., mode='loss'|'predict'|'tensor')` routes to training losses, processed predictions, or raw tensor outputs.

## Registries and Builders

Use these registry nodes from `mmseg.registry`:

- `MODELS`: segmentors, backbones, necks, decode heads, losses, data preprocessors, model wrappers, and related modules.
- `DATASETS`, `TRANSFORMS`, and `DATA_SAMPLERS`: data-side extensions; use the data sub-skill for layout and pipeline details.
- `METRICS` and `EVALUATOR`: validation/test metrics and evaluator wiring.
- `OPTIMIZERS`, `OPTIM_WRAPPERS`, and `OPTIM_WRAPPER_CONSTRUCTORS`: optimizer classes and parameter-group construction.
- `PARAM_SCHEDULERS`: scheduler classes.
- `HOOKS`, `RUNNERS`, `LOOPS`, `VISUALIZERS`, `VISBACKENDS`, `LOG_PROCESSORS`, `INFERENCERS`, and `TASK_UTILS`: advanced runtime and task utilities.

Installed/public API facts:

- `mmseg.models` exports `BACKBONES`, `HEADS`, `LOSSES`, `SEGMENTORS`, `build_backbone`, `build_head`, `build_loss`, `build_segmentor`, and `SegDataPreProcessor`.
- `BACKBONES`, `HEADS`, `LOSSES`, and `SEGMENTORS` are aliases of `MODELS`; the old builder helpers call registry `.build()` and emit deprecation warnings.
- `mmseg.registry` exports 21 registry nodes, including `MODELS`, `DATASETS`, `METRICS`, `RUNNERS`, and `OPTIM_WRAPPER_CONSTRUCTORS`.
- `mmseg.utils.register_all_modules(init_default_scope=True)` imports the MMSegmentation modules and initializes the default scope to `mmseg`.

## Built-in Component Catalog

Do not treat this as exhaustive across every config, but use it to choose the right family before writing custom code.

### Segmentors

- `EncoderDecoder`: standard semantic segmentation model with one decode head and optional auxiliary head.
- `CascadeEncoderDecoder`: multi-stage decode-head cascade.
- `DepthEstimator`: depth prediction variant with `pred_depth_map` behavior.
- `MultimodalEncoderDecoder`: image/text encoder plus decode head for multimodal segmentation.
- `SegTTAModel`: test-time augmentation wrapper.

### Backbones

Source modules include ResNet/ResNeXt/ResNeSt, HRNet, UNet, Fast-SCNN, ICNet, CGNet, ERFNet, BiSeNetV1/V2, DDRNet, STDC, PIDNet, MobileNetV2/V3, Vision Transformer, Swin, Twins, BEiT, MAE, MiT/SegFormer backbone, MSCAN/SegNeXt, VPD, and `TIMMBackbone`.

Selection hints:

- Use ResNet/ResNetV1c-style configs for stable baselines and broad head compatibility.
- Use transformer backbones such as ViT/Swin/BEiT/MiT/MAE when the model zoo config already demonstrates compatible `out_indices`, `embed_dims`, and decode head wiring.
- Use `TIMMBackbone` only when the target environment has the needed timm model and the output feature channels are known.
- Use project backbones only when their project package and optional dependencies are imported successfully.

### Necks

Built-ins include FPN, Feature2Pyramid, JPU, ICNeck, MLANeck, and MultiLevelNeck. Necks must make their output feature tuple/list compatible with the decode head `in_channels`, `in_index`, and `input_transform`.

### Decode Heads

Decode head modules include FCN, PSP, ASPP/DepthwiseSeparableASPP, UPer, FPN, SegFormer, OCR, ISA, ANN, NonLocal, DNL, GC, DM, EMA, Enc, CC, APC, PSA, Point, SETR, Segmenter mask, K-Net, MaskFormer, Mask2Former, SAN, DPT, VPD depth, PID, DDR, STDC, LRASPP, HAM, and cascade base heads.

Important base-head behavior:

- Custom decode heads should usually subclass `BaseDecodeHead`.
- `BaseDecodeHead` validates `in_channels`, `in_index`, and `input_transform` combinations.
- `input_transform=None` selects one feature map and expects integer `in_channels`/`in_index`.
- `input_transform='resize_concat'` resizes selected maps to the first selected map and concatenates channels, so `in_channels` becomes the sum.
- `input_transform='multiple_select'` passes a list of selected feature maps to the head.
- `loss_decode` can be a single loss config or a sequence; loss names that should backpropagate/log conventionally start with `loss_`.
- Binary segmentation can use `out_channels=1` with `num_classes=2` and a threshold; otherwise `out_channels` should equal `num_classes`.

### Losses

Built-ins include CrossEntropy/OHEM cross entropy, Dice, Focal, Lovasz, Tversky, Boundary, Hausdorff distance, KL divergence, SiLog depth loss, and accuracy utilities.

Practical checks:

- Confirm whether the loss expects logits, probabilities, masks, depth values, or one-hot labels.
- Align `ignore_index`, `avg_non_ignore`, `class_weight`, and `use_sigmoid` with dataset labels and decode-head output shape.
- For multiple decode losses, set distinct `loss_name` values if logs need to separate them.

### Data Preprocessor

`SegDataPreProcessor` handles padding, channel conversion, normalization, batch stacking, and optional batch augmentations. Custom preprocessors are `MODELS` entries and are selected in `model.data_preprocessor`.

### Metrics

Metrics register into `METRICS`. Public exports include `IoUMetric`, `CityscapesMetric`, and `DepthMetric`. A custom metric should subclass MMEngine `BaseMetric`, implement `process()` and `compute_metrics()`, and be referenced from `val_evaluator`/`test_evaluator`.

### Optimizers and Schedulers

MMSegmentation uses MMEngine optimizer wrappers. Common configs build parent MMEngine optimizers such as SGD/AdamW through `build_optim_wrapper`. Custom optimizer constructors register into `OPTIM_WRAPPER_CONSTRUCTORS`; layer-decay behavior is implemented by `LearningRateDecayOptimizerConstructor` and is tested against ConvNeXt, BEiT, MAE, and unsupported ViT patterns.

## Model Zoo and Config Selection

The model zoo is config-first. Choose a config family by matching all of these, not just the paper name:

- Dataset and class count.
- Crop size, inference mode, and `align_corners` convention.
- Backbone family and pretrained source.
- Decode head and auxiliary head compatibility.
- Required optional dependencies such as MMDetection for MaskFormer/Mask2Former or MMPretrain-era components.
- Runtime cost: memory, inference mode, and supported hardware.

The repository reports hundreds of checkpoints across algorithms/backbones such as FCN, PSPNet, DeepLabV3/V3+, UPerNet, OCRNet, SegFormer, Segmenter, SETR, Swin, ViT, HRNet, UNet, MaskFormer, Mask2Former, STDC, PIDNet, DPT, SAN, and others. Prefer adapting a nearby config over writing a model dict from scratch.

## Provenance Notes

This reference distills MMSegmentation's public model architecture, registry exports, installed API signatures, and unit-test-backed component behavior into reusable guidance. Treat original repository docs, source modules, and tests as evidence for this bundled reference, not as runtime dependencies for using the skill.
