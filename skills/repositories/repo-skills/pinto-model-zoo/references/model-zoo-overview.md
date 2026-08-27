# PINTO_model_zoo Overview

## Purpose

Read this for a compact, self-contained orientation to PINTO_model_zoo before selecting, downloading, converting, or running a model. Use sub-skills for detailed workflows.

## Repository shape

PINTO_model_zoo is organized around numbered model directories such as `132_YOLOX` or `115_MoveNet`. A directory can contain any mix of:

- `download*.sh` scripts for externally hosted artifacts;
- model files or support files such as `.onnx`, `.tflite`, `.xml`/`.bin`, `.json`, `.npy`, labels, priors, anchors, or test media;
- Python scripts for conversion, quantization, inference, demos, shape editing, postprocess, or runtime tests;
- per-folder `LICENSE`, `README.md`, or notes inherited from the upstream model provider.

The bundled `model-catalog.json` snapshot contains 494 parsed catalog entries across 19 task categories and records format flags from the model-zoo tables. The local source checkout used to create this skill contained 499 numbered model-like directories, more than 1000 shell scripts, and more than 1000 Python scripts; exhaustive per-model instructions are intentionally replaced by catalog and folder-inspection helpers.

## Main task categories

The catalog categories include:

- Image Classification
- 2D Object Detection
- 3D Object Detection
- 2D/3D Face Detection
- 2D/3D Hand Detection
- 2D/3D Human/Animal Pose Estimation
- Depth Estimation from Monocular/Stereo Images
- Semantic Segmentation
- Anomaly Detection
- Artistic
- Super Resolution
- Sound Classifier
- Natural Language Processing
- Text Recognition
- Action Recognition
- Inpainting
- GAN
- Transformer
- Others

Use `scripts/query_model_catalog.py --list-categories` for the exact category strings in the bundled snapshot.

## Format families

The model zoo spans several artifact families:

- **ONNX:** portable graph artifacts and common conversion source/target.
- **TensorFlow / SavedModel / Keras / frozen graph:** historical and conversion workflows.
- **TensorFlow Lite:** FP32, FP16, INT8, dynamic range, weight quantization, full-integer, and EdgeTPU-oriented variants.
- **OpenVINO:** IR `.xml`/`.bin` pairs and CPU/VPU deployments.
- **TensorFlow.js:** browser/WebGL `model.json` and shard workflows.
- **CoreML:** Apple deployment artifacts.
- **TF-TRT / TensorRT:** NVIDIA GPU acceleration workflows.
- **Support artifacts:** labels, priors, anchors, postprocess arrays, metadata, images, and videos.

Catalog flags are availability hints. A selected checkout may still require downloads, optional runtimes, or hardware before the artifact is usable.

## What this skill covers

Covered:

- searching and ranking models by task, name, number, directory, format, and remarks;
- safe download planning and folder inspection;
- runtime/demo dependency and asset preflight;
- conversion/quantization/deployment planning and stop conditions;
- troubleshooting for licenses, network downloads, missing artifacts, optional dependencies, shape/dtype/layout issues, and hardware proof limits.

Not covered as a verified runtime promise:

- exhaustive recipes for every model directory;
- download URL liveness and file checksums;
- legal review of every per-folder license;
- accuracy/FPS claims;
- hardware proof for EdgeTPU, GPU, TF-TRT, browser WebGL, Myriad/VPU, Raspberry Pi, camera, or CoreML device unless a concrete native case is run in a later task.

## Recommended user-facing workflow

1. Select candidate entries with `model-catalog`.
2. Inspect the model folder and download scripts with `model-acquisition`.
3. Prepare runtime/demo checks with `inference-demos`.
4. Plan conversion/quantization/deployment with `conversion-and-deployment` only after confirming that an existing artifact is unavailable or insufficient.
5. Keep blocked items explicit: license, network, storage, assets, optional dependency, dataset, and hardware.
