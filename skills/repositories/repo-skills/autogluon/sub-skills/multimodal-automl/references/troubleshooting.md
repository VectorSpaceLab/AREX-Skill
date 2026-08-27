# MultiModal Troubleshooting

## Fast Diagnosis Order

1. Confirm the request belongs to `MultiModalPredictor`; route structured-only tabular to `../tabular-ml/` and forecasting to `../time-series-forecasting/`.
2. Run `python scripts/multimodal_smoke.py --optional-backends` to inspect imports, versions, problem types, and backend availability without training.
3. Run `python scripts/inspect_multimodal_inputs.py ...` against the user's local data to catch missing columns, unreadable paths, COCO/VOC issues, or ID mapping mismatches.
4. Only then debug model configuration, checkpoint downloads, GPU availability, or training logic.

## Unsupported Problem Type

Symptoms:

- Assertion mentioning `problem_type='...' is not supported`.
- Classification/regression inferred unexpectedly.

Fix:

- Use one of: `classification`, `binary`, `multiclass`, `regression`, `ner`, `named_entity_recognition`, `object_detection`, `text_similarity`, `image_similarity`, `image_text_similarity`, `feature_extraction`, `zero_shot_image_classification`, `few_shot_classification`, `semantic_segmentation`.
- For standard supervised tasks, set `label` and let AutoGluon infer only when labels clearly imply binary/multiclass/regression.
- For semantic matching, always set `problem_type`, `query`, `response`, and usually `match_label`.

## Label, Query, Response, and Candidate Mismatch

Symptoms:

- Missing column errors for `label`, `query`, or `response`.
- Matching scores are nonsensical or all candidates fail.
- `id_mappings` appears ignored.

Fix:

- Ensure constructor column names exactly match DataFrame columns.
- Remove the label column from prediction data but keep it for `fit`/`evaluate` when required.
- For matching labels such as `duplicate`/`not_duplicate`, set `match_label="duplicate"`.
- Use `candidate_data` only for retrieval candidates; use `tuning_data` for validation during `fit`.
- `id_mappings` keys must be the ID column names, and mapped IDs must cover all IDs in data, query data, and candidate/response data.

## Missing Image or Document Paths

Symptoms:

- File-not-found errors.
- All-zero images/documents or unexpectedly poor predictions.
- PDF conversion or OCR failures.

Fix:

- Validate paths with `inspect_multimodal_inputs.py --check-images` or document path checks.
- Make relative paths relative to the process working directory or use absolute paths in user code.
- For document/PDF workflows, install and verify Poppler/PDF conversion and OCR dependencies when required.
- For images embedded as bytes/base64, validate decoding before passing to AutoGluon.

## NER Annotation Errors

Symptoms:

- JSON parsing errors for labels.
- Offset errors or entity spans misaligned with text.
- Multiple text columns confuse the NER processor.

Fix:

- Store labels as JSON lists of objects with `entity_group`, `start`, and `end`.
- Ensure `start`/`end` are character offsets for the exact text string.
- Use `column_types={"text_column": "text_ner"}` when there are multiple text columns.

## Object Detection Class or Annotation Problems

Symptoms:

- Class/head shape mismatch.
- Empty mAP or empty predictions.
- COCO category ID errors.
- VOC conversion skips many boxes.

Fix:

- Pass `sample_data_path` pointing to an annotated split or detection DataFrame.
- Check COCO JSON has `images`, `annotations`, and `categories` for training/evaluation.
- Verify every `annotation.category_id` appears in `categories`.
- Verify every `annotation.image_id` appears in `images`.
- Confirm bounding box format: COCO annotations are `[x, y, width, height]`; RoI DataFrame boxes are commonly `[x1, y1, x2, y2, class_label]`.
- Pass `num_classes` or `classes` explicitly when metadata inference is impossible.

## Optional Backend Problems

Common optional dependencies:

- OCR/PDF/document: Poppler, Tesseract, OCR/PDF Python packages, document transformer checkpoints.
- Object detection: MMDetection, MMCV, pycocotools or torchmetrics.
- ONNX: `onnx`, `onnxruntime` or `onnxruntime-gpu`.
- TensorRT: TensorRT libraries plus compatible CUDA/ONNXRuntime.
- Image stack: matching `torch` and `torchvision` wheels.

Symptoms and fixes:

- `RuntimeError: operator torchvision::nms does not exist`: torch/torchvision wheel mismatch; install matching CPU or CUDA builds.
- `No module named mmcv` or `mmdet`: install the detection stack compatible with the current PyTorch/CUDA versions, or avoid detection training.
- `No module named pycocotools`: install evaluation dependency or use an available evaluation tool.
- `No module named onnxruntime`: install CPU/GPU ONNXRuntime as appropriate.
- TensorRT provider unavailable: verify `onnxruntime-gpu` providers and TensorRT libraries; fall back to CUDA or CPU provider.

## Network and Checkpoint Downloads

Symptoms:

- Training/inference hangs or fails while downloading a model.
- Offline deployment attempts to contact Hugging Face or another model host.

Fix:

- Use `standalone=True` when saving predictors for offline deployment.
- Ask the user for a local checkpoint/cache if the environment has no network.
- Use smaller local checkpoints for smoke testing.
- Set explicit checkpoint names in `hyperparameters` so the dependency is visible.

## GPU vs CPU Expectations

Symptoms:

- CUDA out-of-memory.
- Training too slow on CPU.
- Precision errors on CPU.
- DDP/spawn issues in notebooks or constrained runners.

Fix:

- Set `hyperparameters={"env.num_gpus": 0, "env.precision": 32}` for CPU-only runs.
- Lower batch size via `env.per_gpu_batch_size` and set dataloader workers to `0` in constrained environments.
- Use `time_limit` for smoke runs, but do not claim quality from tiny runs.
- Use GPU for object detection, semantic segmentation, large document models, and high-quality multimodal training when practical.

## Save/Load Problems

Symptoms:

- Load fails on another machine.
- Predictor tries to download assets after load.
- Resume fails after interrupted training.

Fix:

- Save with `standalone=True` when model assets must travel with the predictor.
- Use `MultiModalPredictor.load(path, resume=True)` only for interrupted training checkpoints.
- Treat loaded predictors as trusted artifacts only; pickle-backed loading is unsafe for untrusted files.
- Recreate a compatible AutoGluon/PyTorch environment when moving between machines.

## Smoke Commands

```bash
python scripts/multimodal_smoke.py
python scripts/multimodal_smoke.py --optional-backends
python scripts/inspect_multimodal_inputs.py --csv train.csv --label label --image-columns image --check-images
python scripts/inspect_multimodal_inputs.py --coco annotations/train.json --image-root . --check-images
```
