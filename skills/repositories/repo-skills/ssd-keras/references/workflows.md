# Workflow Guide

This repository is notebook-driven, but the bundled skill scripts provide the safest reusable path for day-to-day work. Use the route that matches the task, then open the supporting references for the object and data contracts.

## Fast chooser

- Need to parse or validate data: go to `data-preparation`.
- Need to build or train a model: go to `training`.
- Need to run predictions, decode boxes, or compute mAP: go to `inference-evaluation`.
- Need a quick confidence check: run `scripts/check_env.py` first, then the relevant smoke script.

## Training SSD300 on VOC

1. Confirm the environment with `scripts/check_env.py`.
2. Read `references/model-architecture.md` for `ssd_300`, `SSDLoss`, and `SSDInputEncoder`.
3. Prepare the dataset in the format described in `references/data-formats.md`.
4. Build the model in `training` mode and load pretrained VGG or SSD weights by name.
5. Configure the encoder so that scales, aspect ratios, steps, offsets, coordinate normalization, and classes match the model.
6. Compile with `SSDLoss.compute_loss` and the optimizer you want to use.
7. Fit from a generator that yields encoded labels and processed images.
8. Save checkpoints and monitor for `OOM` or `NaN` issues early in training.

Good notebook evidence:

- `ssd300_training.ipynb`
- `training_summaries/ssd300_pascal_07+12_training_summary.md`

## Training SSD7 or a custom backbone

1. Use `models/keras_ssd7.py` as the template builder.
2. Pick the smaller SSD7 path when you only need a fast smoke or a less expensive training setup.
3. Use the same encoder / loss contract as for SSD300.
4. If the class count changes, adapt the classifier weights with `sample_tensors` before loading them into the new head.

Good notebook evidence:

- `ssd7_training.ipynb`
- `weight_sampling_tutorial.ipynb`

## Running inference

1. Build the model in `inference` or `inference_fast` mode.
2. Load the trained weights or a saved model with the required custom objects.
3. Prepare a batch of images with `DataGenerator` and a resize / channel-conversion chain.
4. Run `model.predict(...)`.
5. If the model is still in training mode, decode the raw tensor with `decode_detections` or `decode_detections_fast`.
6. Convert predictions back to the original image frame with `apply_inverse_transforms` when the input images were transformed.

Good notebook evidence:

- `ssd300_inference.ipynb`
- `ssd512_inference.ipynb`

## Evaluating VOC mAP

1. Build or load the trained model.
2. Instantiate `DataGenerator` with VOC XML data or another compatible dataset.
3. Create an `Evaluator` with the correct `model_mode`.
4. Choose `average_precision_mode='sample'` for VOC 2007-style evaluation or `average_precision_mode='integrate'` for later VOC-style integration.
5. Run the evaluator and inspect per-class AP, precision, recall, and mean AP.

Good notebook evidence:

- `ssd300_evaluation.ipynb`

## Exporting COCO predictions

1. Parse the COCO-style categories and annotations.
2. Map model class IDs to the original COCO category IDs.
3. Run `predict_all_to_json(...)` to create the results file.
4. Evaluate the JSON file with COCO tooling when `pycocotools` is available.

Good notebook evidence:

- `ssd300_evaluation_COCO.ipynb`

## Weight sampling and transfer learning

1. Inspect the source classifier tensor shapes in the pretrained weights file.
2. Choose the classes to keep in the target model.
3. Use `sample_tensors(...)` to sub-sample or up-sample the classifier kernels and biases consistently.
4. Verify that the sampled weights still load into the new model head.

Good notebook evidence:

- `weight_sampling_tutorial.ipynb`

## Smoke scripts

Use these bundled helpers instead of opening the original notebooks when you only need a quick runtime check. They resolve their imports from the skill's bundled `runtime-src/` tree, not from a local checkout:

- `scripts/check_env.py` — import and version smoke for the environment.
- `sub-skills/data-preparation/scripts/smoke.py` — synthetic dataset parsing and batch generation.
- `sub-skills/training/scripts/smoke.py` — model build, encoder, loss, and tiny train-step smoke.
- `sub-skills/inference-evaluation/scripts/smoke.py` — decoding and evaluation smoke on synthetic predictions.

## Practical reminder

The notebooks are the historical source of truth for the full recipes, but the skill should rely on the bundled references and scripts for repeatable work. If a notebook and a reference disagree, trust the live source code plus the verified inspection environment over the prose summary.
