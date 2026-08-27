# Component API reference

This page distills the MMOCR 1.x component contracts needed for extension and component-level debugging. It is self-contained: do not rely on the source checkout being present when applying these rules.

## Registry model and default scope

MMOCR uses MMEngine registries. Components are available only after their defining Python modules have been imported. For core MMOCR modules, `mmocr.utils.register_all_modules(init_default_scope=True)` imports the core subpackages and sets the default scope to `mmocr`; use `init_default_scope=False` when another OpenMMLab project owns the current scope and you only need imports.

Core registry nodes defined by `mmocr.registry`:

| Registry | Primary use | Module locations |
| --- | --- | --- |
| `RUNNERS`, `RUNNER_CONSTRUCTORS`, `LOOPS`, `HOOKS`, `LOG_PROCESSORS` | Engine integration | `mmocr.engine`, `mmocr.engine.hooks` |
| `DATASETS`, `DATA_SAMPLERS`, `TRANSFORMS` | Datasets, samplers, data pipelines | `mmocr.datasets`, `mmocr.datasets.samplers`, `mmocr.datasets.transforms` |
| `MODELS`, `MODEL_WRAPPERS`, `WEIGHT_INITIALIZERS` | Neural modules, detectors, recognizers, preprocessors, heads, losses, postprocessors | `mmocr.models` |
| `OPTIMIZERS`, `OPTIM_WRAPPERS`, `OPTIM_WRAPPER_CONSTRUCTORS`, `PARAM_SCHEDULERS` | Optimizer and scheduler config integration | `mmocr.engine` |
| `METRICS`, `EVALUATOR` | Validation/test metrics and evaluators | `mmocr.evaluation.metrics`, `mmocr.evaluation.evaluator` |
| `TASK_UTILS` | Non-`nn.Module` task utilities such as dictionaries and parsers | `mmocr.models`, `mmocr.utils` |
| `VISUALIZERS`, `VISBACKENDS` | Local visualizers and visualization backends | `mmocr.visualization` |
| `DATA_OBTAINERS`, `DATA_GATHERERS`, `DATA_PARSERS`, `DATA_PACKERS`, `DATA_DUMPERS`, `CFG_GENERATORS` | Dataset-preparer internals | `mmocr.datasets.preparers.*` |

Dynamic registration checklist:

1. Ensure the Python package that defines the class is importable.
2. Decorate classes with the correct registry, for example `@MODELS.register_module()`, `@TRANSFORMS.register_module()`, `@METRICS.register_module()`, or `@VISUALIZERS.register_module()`.
3. Import the module before calling `MODELS.build`, `TRANSFORMS.build`, `METRICS.build`, or config-driven Runner construction. In config files this is normally done with `custom_imports = dict(imports=[...], allow_failed_imports=False)`.
4. Keep `default_scope = 'mmocr'` or initialize a compatible MMEngine `DefaultScope` when building unqualified types such as `DBNet`, `Dictionary`, `LoadOCRAnnotations`, or `HmeanIOUMetric`.
5. If a class name collides with another OpenMMLab package, use the intended scope or an explicit import path instead of relying on whatever scope happens to be current.

## DataSample contracts

MMOCR component APIs pass typed MMEngine data elements between transforms, models, postprocessors, metrics, and visualizers. Set the correct data element type; the property setters enforce this.

| Task | DataSample class | Main fields | Payload types | Typical readers/writers |
| --- | --- | --- | --- | --- |
| Text detection | `TextDetDataSample` | `gt_instances`, `pred_instances` | `mmengine.structures.InstanceData` | Detection pack transforms, detectors, textdet postprocessors, `HmeanIOUMetric`, `TextDetLocalVisualizer` |
| Text spotting | `TextSpottingDataSample` | `gt_instances`, `pred_instances` | Inherits text-detection sample behavior | E2E spotting postprocessors, spotting metrics/visualizers, contributed projects such as ABCNet/SPTS |
| Text recognition | `TextRecogDataSample` | `gt_text`, `pred_text` | `mmengine.structures.LabelData` | Recognition pack transforms, decoders/postprocessors, text-recognition metrics, `TextRecogLocalVisualizer` |
| Key information extraction | `KIEDataSample` | `gt_instances`, `pred_instances` | `InstanceData` | KIE transforms, SDMGR, `F1Metric`, `KIELocalVisualizer` |

### InstanceData fields by task

All per-instance fields in one `InstanceData` should describe the same number of instances `N` unless explicitly optional.

| Field | TextDet | TextSpotting | KIE | Meaning |
| --- | --- | --- | --- | --- |
| `bboxes` | yes | yes | yes | Float tensor/array shaped `(N, 4)` in `[x1, y1, x2, y2]` convention. |
| `polygons` | yes | yes | optional | List of float arrays, one polygon per instance. Detection and spotting visualizers prefer polygons when present. |
| `labels` | yes | optional | yes | Integer node/class labels. Text detection normally uses class id `0` for text. |
| `scores` | predictions | predictions | predictions | Confidence scores for predicted instances or node labels. |
| `ignored` | ground truth | ground truth | optional | Boolean flags for ignored text instances. Detection metrics and visualizers treat ignored instances specially. |
| `texts` | optional | yes | yes | Text strings attached to instances. Required by spotting visualizers and KIE visualizers. |
| `text_scores` | predictions | predictions | no | Recognition confidence per spotted text instance. |
| `edge_labels` | no | no | yes | KIE adjacency/relationship matrix shaped `(N, N)`, commonly values `-1`, `0`, and `1` for ignored, disconnected, connected. |
| `edge_scores` | no | no | predictions | KIE edge confidence matrix shaped `(N, N)`. |
| `relations` | no | no | optional | Relation annotations used by KIE tests and some datasets. |

### LabelData fields for recognition

`TextRecogDataSample.gt_text` and `TextRecogDataSample.pred_text` are `LabelData` objects.

| Field | Meaning |
| --- | --- |
| `item` | The decoded string. Metrics and visualizers expect this for both ground truth and predictions. |
| `score` | List or tensor of character/text confidence scores for predictions. |
| `indexes` | Character indexes produced from a `Dictionary`. |
| `padded_indexes` | Index sequence padded to a model-specific maximum length when a padding token exists. |

### Choosing fields in custom postprocessors and visualizers

- Detection postprocessors should return the same `TextDetDataSample` instance or a new one with `pred_instances.polygons` or `pred_instances.bboxes`, plus `pred_instances.scores`. If rescaling is enabled, only put rescalable polygon/bbox fields in `rescale_fields`.
- Recognition postprocessors should fill `pred_text.item` and `pred_text.score`; the base recognition postprocessor already converts predicted indexes through a `Dictionary` and writes `LabelData`.
- KIE postprocessors should fill `pred_instances.labels`, `pred_instances.scores`, `pred_instances.edge_labels`, and `pred_instances.edge_scores`; KIE visualizers still read ground-truth `bboxes` and `texts` for layout.
- Text spotting components should keep geometry in `pred_instances.polygons` or `pred_instances.bboxes`, strings in `pred_instances.texts`, and detection confidences in `pred_instances.scores`.

## Model component families

Most model-side components are registered in `MODELS`.

### Common components

- `Dictionary` is registered in `TASK_UTILS`, not `MODELS`.
- Shared backbones include `UNet` and `CLIPResNet`.
- Shared losses include balanced/masked BCE variants, Dice losses, smooth L1 variants, and cross entropy.
- Transformer layers/modules include `TFEncoderLayer`, `TFDecoderLayer`, `ScaledDotProductAttention`, `MultiHeadAttention`, `PositionwiseFeedForward`, and `PositionalEncoding`.

### Text detection components

- Detectors: `SingleStageTextDetector`, `DBNet`, `PANet`, `PSENet`, `TextSnake`, `FCENet`, `DRRG`, `MMDetWrapper`.
- Data preprocessor: `TextDetDataPreprocessor`.
- Necks: `FPEM_FFM`, `FPNF`, `FPNC`, `FPN_UNet`.
- Heads: `BaseTextDetHead`, `PSEHead`, `PANHead`, `DBHead`, `FCEHead`, `TextSnakeHead`, `DRRGHead`.
- Module losses: `SegBasedModuleLoss`, `PANModuleLoss`, `PSEModuleLoss`, `DBModuleLoss`, `TextSnakeModuleLoss`, `FCEModuleLoss`, `DRRGModuleLoss`.
- Postprocessors: `BaseTextDetPostProcessor`, `PSEPostprocessor`, `PANPostprocessor`, `DBPostprocessor`, `DRRGPostprocessor`, `FCEPostprocessor`, `TextSnakePostprocessor`.

### Text recognition components

- Recognizers: `BaseRecognizer`, `EncoderDecoderRecognizer`, `CRNN`, `SARNet`, `NRTR`, `RobustScanner`, `SATRN`, `ABINet`, `MASTER`, `SVTR`, `ASTER`, `EncoderDecoderRecognizerTTAModel`.
- Data preprocessor: `TextRecogDataPreprocessor`.
- Backbones: `ResNet31OCR`, `MiniVGG`, `NRTRModalityTransform`, `ShallowCNN`, `ResNetABI`, `ResNet`, `MobileNetV2`.
- Preprocessors/plugins: `STN`, `TPStransform`, `Maxpool2d`, `GCAModule`.
- Encoders: `BaseEncoder`, `SAREncoder`, `NRTREncoder`, `ChannelReductionEncoder`, `SATRNEncoder`, `ABIEncoder`, `SVTREncoder`, `ASTEREncoder`.
- Decoders/fusers: `BaseDecoder`, `CRNNDecoder`, `ParallelSARDecoder`, `SequentialSARDecoder`, `ParallelSARDecoderWithBS`, `NRTRDecoder`, `SequenceAttentionDecoder`, `PositionAttentionDecoder`, `ABILanguageDecoder`, `ABIVisionDecoder`, `MasterDecoder`, `RobustScannerFuser`, `ABIFuser`, `SVTRDecoder`, `ASTERDecoder`.
- Module losses: `BaseTextRecogModuleLoss`, `CEModuleLoss`, `CTCModuleLoss`, `ABIModuleLoss`.
- Postprocessors: `BaseTextRecogPostprocessor`, `AttentionPostprocessor`, `CTCPostProcessor`.

### KIE components

KIE support is centered on SDMGR:

- Extractor/model: `SDMGR`.
- Head: `SDMGRHead`.
- Module loss: `SDMGRModuleLoss`.
- Postprocessor: `SDMGRPostProcessor`, including open-set edge reconstruction modes `one-to-one`, `one-to-many`, `many-to-one`, `many-to-many`, and `none`.

## Dictionaries and recognition token handling

Bundled dictionary files include:

- `chinese_english_digits.txt`
- `english_digits_symbols.txt`
- `english_digits_symbols_space.txt`
- `korean_english_digits_symbols.txt`
- `lower_english_digits.txt`
- `lower_english_digits_space.txt`
- `sdmgr_dict.txt`

`Dictionary` rules:

- A dictionary file is line-oriented; each non-empty line must contain exactly one character. Multi-character entries raise an error.
- Duplicate characters are rejected.
- Special tokens are appended after file characters according to flags: `with_start`, `with_end`, `same_start_end`, `with_padding`, and `with_unknown`.
- Default token strings are `<BOS>`, `<EOS>`, `<BOS/EOS>`, `<PAD>`, and `<UKN>`.
- `char2idx(char, strict=True)` raises on unknown characters unless `with_unknown=True` or `strict=False`.
- `str2idx(text)` encodes character-by-character; it can skip unknowns only when `with_unknown=True` and the unknown token index is absent.
- `idx2str(indexes)` asserts each index is within the dictionary length and concatenates token strings.
- Recognition postprocessors can ignore indexes mapped from `padding`, `end`, `unknown`, or literal characters; an ignored symbol not present in the dictionary produces a warning.

Synchronization rules:

- Decoder output dimension must equal `dictionary.num_classes` after special tokens are appended.
- CTC-style models usually need a padding/blank token; attention-style models usually need start/end tokens. Match the model config and postprocessor ignore rules.
- Ground-truth strings must be representable by the dictionary unless unknown handling is intentional.
- If a project supplies its own dictionary, package it with the project or pass a stable path from the calling application; do not assume the source repository layout is available.

## Transform and pipeline components

Pipeline transforms are registered in `TRANSFORMS`. They operate on mutable dictionaries before packaging into model inputs and `DataSample` objects.

Common pipeline keys:

| Key | Meaning |
| --- | --- |
| `img`, `img_path`, `img_shape`, `ori_shape` | Image array/path and current/original image shape. |
| `scale`, `scale_factor`, `keep_ratio`, `flip`, `flip_direction` | Resize/flip metadata consumed by postprocessors and transforms. |
| `gt_bboxes`, `gt_polygons`, `gt_bboxes_labels`, `gt_ignored`, `gt_texts` | Text detection/spotting annotations before packing. |
| `gt_edge_labels` | KIE relation annotations before packing. |

Transform families:

- Loading: `LoadImageFromFile`, `LoadImageFromNDArray`, `InferencerLoader`, `LoadOCRAnnotations`, `LoadKIEAnnotations`.
- OCR-generic augmentation: `RandomCrop`, `RandomRotate`, `Resize`, `FixInvalidPolygon`, `RemoveIgnored`.
- Text-detection augmentation: `BoundedScaleAspectJitter`, `RandomFlip`, `SourceImagePad`, `ShortScaleAspectJitter`, `TextDetRandomCrop`, `TextDetRandomCropFlip`.
- Text-recognition augmentation: `PyramidRescale`, `RescaleToHeight`, `PadToWidth`, `TextRecogGeneralAug`, `CropHeight`, `ImageContentJitter`, `ReversePixels`.
- Formatting: `PackTextDetInputs`, `PackTextRecogInputs`, `PackKIEInputs`; these create the appropriate `DataSample` type and move annotation fields into `gt_instances` or `gt_text`.
- Cross-project adapters: `MMDet2MMOCR`, `MMOCR2MMDet` for moving polygon/mask/ignore fields between MMDetection and MMOCR conventions.
- Third-party wrappers: `ImgAugWrapper`, `TorchVisionWrapper`, and `ConditionApply`.

When composing a pipeline, check each transform's required/modified/added keys. A transform type lookup failure usually means the transform package was not imported, the `mmocr` scope is not active, or the class name is misspelled.

## Metrics and evaluator outputs

Metrics are registered in `METRICS` and are normally placed in validation/test evaluator configs.

| Metric | Task | Inputs expected from `DataSample` | Main outputs |
| --- | --- | --- | --- |
| `HmeanIOUMetric` | Text detection | Prediction/GT polygons and detection scores; ignored GT is filtered | `recall`, `precision`, `hmean`; can search score thresholds and supports `vanilla` or `max_matching` pairing. |
| `WordMetric` | Text recognition | `pred_text.item`, `gt_text.item` | `word_acc`, `word_acc_ignore_case`, `word_acc_ignore_case_symbol` depending on `mode`. |
| `CharMetric` | Text recognition | `pred_text.item`, `gt_text.item` | `char_recall`, `char_precision`; case-insensitive character scoring. |
| `OneMinusNEDMetric` | Text recognition | `pred_text.item`, `gt_text.item` | `1-N.E.D`, useful for long text-line predictions. |
| `F1Metric` | KIE | Predicted/GT labels | `macro_f1`, `micro_f1` depending on `mode`. |

Custom metric pattern: subclass MMEngine `BaseMetric`, implement `process(data_batch, predictions)` and `compute_metrics(results)`, register with `@METRICS.register_module()`, and return a dictionary with stable scalar keys.

`MultiDatasetsEvaluator` supports per-dataset metric evaluation when multiple datasets are combined; ensure output prefixes do not collide.

## Visualizers

Visualizers are registered in `VISUALIZERS` and consume the same `DataSample` fields used by metrics.

| Visualizer | Expected sample fields | Notes |
| --- | --- | --- |
| `BaseLocalVisualizer` | Direct helper methods for labels, polygons, bboxes, arrows | Supports `font_properties` for non-Latin text; inherited by task visualizers. |
| `TextDetLocalVisualizer` | `gt_instances` / `pred_instances` with `polygons` or `bboxes`, `scores`, optional `ignored` | Filters predictions by `pred_score_thr`; can draw polygons and/or boxes. |
| `TextRecogLocalVisualizer` | `gt_text.item`, `pred_text.item` | Renders resized image plus text panels. |
| `TextSpottingLocalVisualizer` | Geometry plus `texts` in instances | Uses polygons if present; derives boxes from polygons when needed. |
| `KIELocalVisualizer` | `gt_instances.bboxes`, `gt_instances.texts`, GT/pred `labels`, optional `edge_labels`, dataset `category` metainfo | Open-set mode adds edge arrows; predicted labels are drawn on GT layout. |

Headless usage rules:

- Prefer `show=False` and `out_file`/backend saving for non-interactive runs.
- Supply a font file through `font_properties` when drawing Chinese, Korean, or other glyphs not covered by default fonts.
- Use RGB images for visualizer inputs; saved images are converted internally when needed.

## Utilities relevant to component work

- `register_all_modules` imports MMOCR modules and manages default scope.
- Geometry helpers include bbox, polygon, Bezier, mask, point, image crop/warp, and line-stitching utilities.
- Parsers `LineJsonParser` and `LineStrParser` are task utilities registered in `TASK_UTILS` and used for annotation parsing.
- `remove_pipeline_elements` can help manipulate pipeline configs by transform type when adapting configs programmatically.

## Component probe script

The bundled `scripts/mmocr_component_registry_probe.py` is a runtime helper for quick component checks. It can:

- import MMOCR registries;
- optionally call `register_all_modules`;
- print registry names and approximate module counts;
- verify availability of the four `DataSample` classes;
- list dictionary files from a caller-provided directory without assuming a source checkout.

Use it as a smoke check for the active Python environment before debugging deeper component failures.
