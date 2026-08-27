# Model Catalog and Selection Guide

Use this catalog after selecting the correct preparation helper in [learn-workflows](learn-workflows.md). Model names below are distilled from deep-learning guide notebooks, GPU-tagged data-science samples, and import-name counts; they are evidence-backed but not GPU-training-verified in this inspection environment.

## Fast selection rules

| If the task looks like this | Prefer these families first |
| --- | --- |
| Pixel-wise land cover, building footprint, slum, stream, or hyperspectral segmentation | `UnetClassifier`, `DeepLabV3`, `PSPNet`, `CLIMAX`, `FeatureClassifier` variants |
| Instance masks or object instances with masks | `MaskRCNN` |
| Bounding boxes or object detectors | `SingleShotDetector`, `FasterRCNN`, `YOLOv3`, `RetinaNet`, `RT-DETRv2`, MMDetection adapters |
| Before/after imagery comparison | `ChangeDetector` |
| Low-resolution to high-resolution imagery | `SuperResolution`, SR3-style SuperResolution paths |
| Paired image-to-image translation | `Pix2Pix` |
| Unpaired image-to-image translation | `CycleGAN` |
| Video object tracking | `ObjectTracker` or detector `predict_video(..., track=True)` patterns |
| Text classes | `TextClassifier` |
| Named entities or spans | `EntityRecognizer` |
| Address correction or custom text generation | `SequenceToSequence` or custom NLP model-extension paths |
| Tabular prediction or unsupervised ML | `MLModel`, `FullyConnectedNetwork`, `AutoML` |
| Sequence/time forecasting | `TimeSeriesModel` |
| 3D point-cloud classification/segmentation/object detection | `PointCNN`, `PointTransformer`, `RandLA-Net`, `SQN`, `SECOND` |
| A third-party model/framework must be integrated | `ModelExtension`, `MMDetection`, `MMSegmentation`, `SAM`/`SamLoRA` |

## Vision and imagery families

- `UnetClassifier` — Use for semantic segmentation where labels are pixel masks. Evidence includes U-Net guide material plus samples for building footprints, slums, sparse land-cover labels, and hyperspectral land cover. Prep helper: `prepare_data`.
- `MaskRCNN` — Use for instance segmentation and object masks, including buildings and bathymetric/shipwreck examples. Prep helper: `prepare_data`; export format usually needs instance masks rather than ordinary class rasters.
- `SingleShotDetector` — Use for fast object detection with bounding boxes. Evidence includes SSD guide material plus road-surface and brick-kiln samples. Prep helper: `prepare_data`.
- `FasterRCNN` — Use when region-proposal detection or a torchvision/custom detector bridge is intended. Evidence includes Faster R-CNN guide material, window/door retraining, multi-GPU support lists, and a `ModelExtension` custom FasterRCNN example. Prep helper: `prepare_data`; extension path: `ModelExtension`.
- `YOLOv3` — Use for single-pass object detection where the notebook/request names YOLO. Evidence includes the YOLOv3 object-detector guide and AutoDL detector lists. Prep helper: `prepare_data`.
- `RetinaNet` — Use for one-shot object detection and detector-backed tracking workflows. Evidence includes RetinaNet guide material, vehicle detection/tracking samples, tensorboard monitoring lists, and RT-DETRv2 comparison text. Prep helper: `prepare_data`.
- `ChangeDetector` — Use for before/after image-pair change detection. Evidence includes building-change notebooks and change-detection guides. Prep helper: `prepare_data` with paired before/after imagery layout.
- `SuperResolution` — Use for upsampling/restoring image detail, including SR3-style guide material. Evidence includes SuperResolution guide notebooks and image-resolution samples. Prep helper: `prepare_data` with low/high-resolution image pairs.
- `CycleGAN` — Use for unpaired image-to-image translation, such as SAR-to-RGB translation where the domains are not aligned pairwise. Prep helper: `prepare_data`.
- `Pix2Pix` — Use for paired image-to-image translation, such as DSM-to-RGB or Landsat-to-Sentinel style examples. Prep helper: `prepare_data`.
- `MultiTaskRoadExtractor` and `ConnectNet` — Use for road/stream extraction workflows where the notebook names these families. Prep helper: `prepare_data`; check chip size and export layout carefully.
- `BDCNEdgeDetector` and `HEDEdgeDetector` — Use for edge/boundary extraction such as parcel extraction. Prep helper: `prepare_data`; backbones are dependency-sensitive.
- `ObjectTracker` and SiamMask-style tracking — Use for multi-object tracking or detector-backed video tracking. Evidence includes object-tracker and video detection/tracking notebooks. Expect video files and metadata; do not treat tracking as simple raster inference.
- Additional guide-observed image families include `DeepLabV3`, `PSPNet`, `CLIMAX`, `FeatureClassifier`, `ImageCaptioner`, `WNet-CGAN`, `MaxDeepLab`, `ATSS`, and `RT-DETRv2`. Use them only when the requested notebook pattern or user requirement names the family, because their dependencies and data formats vary.

## Text and NLP families

- `TextClassifier` — Use when every document or text row has one or more class labels. Prep helper: `prepare_textdata`. Evidence includes text-classification, country-name classification, third-party language-model, and Mistral-backed classification notebooks.
- `EntityRecognizer` — Use for named-entity recognition where labels are spans/entities inside documents. Prep helper: `prepare_textdata`. Evidence includes NER guide notebooks, crime-incident information extraction, doccano labeling, custom GLiNER-style `.dlpk`, and Mistral-backed NER notebooks.
- `SequenceToSequence` — Use for address standardization/correction or text transformation where inputs map to output sequences. Prep helper: `prepare_textdata` or a custom NLP package; verify the required export format before training.
- Third-party NLP functions — Use `ModelExtension` or `.dlpk` loading paths when the notebook/request supplies an external model such as a transformer or custom inference function. Do not assume those dependencies exist just because `arcgis.learn.text` imports.

## Tabular, AutoML, and time-series families

- `MLModel` — Use for classical/scikit-learn-style regression, classification, or unsupervised tabular models exposed through `arcgis.learn`. Prep helper: `prepare_tabulardata`; validate target field, explanatory variables, categorical handling, and spatially enabled DataFrame schema.
- `FullyConnectedNetwork` — Use for neural tabular regression/classification where the notebook pattern uses dense-network training rather than a classical model wrapper. Prep helper: `prepare_tabulardata`.
- `AutoML` — Use for automated tabular model search. Evidence includes supervised tabular AutoML samples. It is a workflow assistant, not a guarantee that the resulting model is deployable without the selected backend.
- `AutoDL` — Use for automated image architecture search when the guide/sample explicitly asks to compare multiple supported image networks. Evidence includes AutoDL guide material and automated swimming-pool detection. It is an orchestration helper over image families, not a substitute for data-prep validation.
- `TimeSeriesModel` — Use for forecasting from tabular time-series sequences. Prep helper: `prepare_tabulardata`; guide evidence includes univariate/multivariate forecasting and architectures such as `InceptionTime`, `ResCNN`, `ResNet`, and `FCN`.

## Point-cloud and 3D families

- `PointCNN` — Use for point-cloud segmentation/classification guide patterns. Prep helper: `prepare_data(..., dataset_type=...)` with the appropriate point-cloud dataset type.
- `PointTransformer` — Use when the requested point-cloud classification guide names Point Transformer. Verify point attributes, class labels, and memory footprint before fitting.
- `RandLA-Net` — Use for point-cloud classification where the RandLA-Net notebook pattern is requested. Treat GPU/runtime requirements as advanced.
- `SQN` — Use for sparse-query-network point-cloud classification patterns, especially sparse-label examples. Verify sparse-label format and neighborhood settings.
- `SECOND` — Use for point-cloud object detection. Evidence includes `MMDetection3D`/`SECOND` notebook patterns; do not use it for ordinary 2D imagery boxes.

## Framework adapters and model extensibility

- `ModelExtension` — Use to integrate a custom Python model class with the `arcgis.learn` training/saving/inference contract. Evidence includes a custom FasterRCNN extension plus NLP extension notebooks. The custom class must satisfy the expected interface and import all external dependencies.
- `MMDetection` — Use when the request needs an external MMDetection detector, named supported model, or explicit config/weight files. Evidence includes `MMDetection.supported_models` and config/weight examples. This path requires the MMDetection stack and compatible model weights.
- `MMSegmentation` — Use for external MMSegmentation semantic segmentation adapters. Evidence includes named model examples and supported-model inspection. This path requires the MMSegmentation stack.
- `SAM` and `SamLoRA` — Use for Segment Anything fine-tuning/adaptation when the request names SAM or SamLoRA. Evidence includes the SamLoRA fine-tuning notebook. Treat pretrained weights, GPU memory, and dependency versioning as required gates.

## Selection cautions

- Do not choose a model solely from the notebook title; match label geometry, input data type, deployment target, and dependency stack.
- Do not downgrade a GPU-tagged training workflow to CPU and call it verified. At most, CPU can support planning or import-only checks.
- Do not route non-learning raster analytics here. If there is no learned model, use imagery-raster-analysis.
- Do not route generic feature engineering, feature-layer editing, or SEDF analysis here unless the table rows are being used as training data for `prepare_tabulardata`.
