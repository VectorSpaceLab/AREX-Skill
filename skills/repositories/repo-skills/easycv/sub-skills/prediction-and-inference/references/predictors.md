# Predictor family

EasyCV predictors share a small set of constructor patterns:

- `model_path`
- optional `config_file`
- `batch_size`
- `device`
- `save_results` / `save_path`
- `pipelines`
- `input_processor_threads`
- `mode`

## Shared base contracts

- `PredictorInterface` is the older batch interface used by some legacy wrappers.
- `PredictorInterfaceV2` is the newer dict-based input interface.
- `PredictorV2.__call__(inputs, keep_inputs=False)` is the main batch path for the modern predictor stack.

## Major predictor groups

| Group | Representative classes | Typical extra args | Notes |
| --- | --- | --- | --- |
| Classification | `ClassificationPredictor`, `TorchClassifier`, `ReIDPredictor`, `VideoClassificationPredictor`, `TorchFeatureExtractor`, `TorchFaceFeatureExtractor`, `TorchMultiFaceFeatureExtractor`, `TorchFaceAttrExtractor` | `topk`, `pil_input`, `label_map_path`, `multi_class`, `with_text` | Use for image, video, retrieval, and feature extraction workflows. |
| Detection | `DetectionPredictor`, `YoloXPredictor`, `TorchYoloXPredictor`, `TorchFaceDetector`, `TorchYoloXClassifierPredictor` | `score_threshold`, `model_type`, `jit_processor_path`, `use_trt_efficientnms` | Use for object detection and YOLOX-style export artifacts. |
| Segmentation | `SegmentationPredictor`, `Mask2formerPredictor` | `task_mode` | Use for semantic, instance, and panoptic masks. |
| Pose | `PoseTopDownPredictor`, `TorchPoseTopDownPredictorWithDetector`, `WholeBodyKeypointsPredictor`, `HandKeypointsPredictor`, `FaceKeypointsPredictor` | `detection_predictor_config`, `bbox_thr`, `cat_id`, `model_type` | Use for keypoints workflows, often with a detector-on-top pipeline. |
| OCR | `OCRPredictor`, `OCRDetPredictor`, `OCRRecPredictor`, `OCRClsPredictor` | `det_batch_size`, `rec_batch_size`, `cls_batch_size`, `drop_score`, `use_angle_cls` | Use for multi-stage OCR pipelines. |
| 3D / specialized | `BEVFormerPredictor`, `MOTPredictor` | task-specific config | Use when the model and dataset are task-specific rather than generic image classification. |

## Model-type notes

- `raw` checkpoints load through the normal EasyCV model path.
- `jit` and `blade` artifacts usually need a config sidecar.
- Some predictor variants infer their model type from the filename suffix.
- `onnx` paths follow a slightly different config / sidecar convention.

## Common output shapes

- Classification: `class`, `class_name`, `class_probs`
- Detection: `detection_boxes`, `detection_scores`, `detection_classes`, `detection_class_names`
- Segmentation: `seg_pred`, `masks`, `labels`, `labels_ids`, `bboxes`, `scores`
- Pose: `keypoints`, `bbox`
- Feature extraction: `feature`
- OCR: nested detection / recognition / classification results

## Good usage rule

Pick the predictor class from the output you want first, not from the input format. A detector-style artifact and a classifier-style artifact need different predictors even when they both end in `.pth`.

