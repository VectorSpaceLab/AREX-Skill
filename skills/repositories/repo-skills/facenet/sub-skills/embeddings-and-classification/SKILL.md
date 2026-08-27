---
name: embeddings-and-classification
description: "Use Facenet embeddings for face comparison, SVM classifiers,
  embedding export, clustering, and contributed recognition examples."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Facenet Embeddings and Classification

Use this sub-skill when a task starts from a trained Facenet model and asks for embeddings, face comparison, classifier training/classification, batch export, clustering, or contributed high-level recognition examples.

## When to read

- The user asks to compare faces or print a distance matrix.
- The user wants to train a classifier on identity folders or classify held-out images.
- The task needs exported `embeddings.npy`, `labels.npy`, or label strings.
- The user asks to cluster similar faces from a folder.
- The request mentions `compare`, `classifier`, `export_embeddings`, `batch_represent`, `cluster`, `predict`, or real-time face recognition.

## Prerequisites

1. A Facenet TF1 environment that imports `facenet`, `align.detect_face`, TensorFlow, NumPy, SciPy, scikit-learn, and OpenCV.
2. A model path accepted by Facenet: checkpoint directory or frozen `.pb`. Read [`../model-export-and-checkpoints/SKILL.md`](../model-export-and-checkpoints/SKILL.md) for model formats.
3. Aligned class-folder data for classifier/export workflows. If input images are raw photos, read [`../data-and-alignment/SKILL.md`](../data-and-alignment/SKILL.md) first.
4. Enough images per identity for classifier splitting; defaults in `classifier` require at least 20 images per class when `--use_split_dataset` is enabled.

## Workflow map

- **Compare images**: use [`scripts/build_compare_command.py`](scripts/build_compare_command.py), then read [`references/workflows.md`](references/workflows.md#compare-images).
- **Train or use an SVM classifier**: use [`scripts/build_classifier_command.py`](scripts/build_classifier_command.py), then read [`references/workflows.md`](references/workflows.md#train-or-use-an-svm-classifier).
- **Export embeddings as NumPy arrays**: use [`scripts/build_export_embeddings_command.py`](scripts/build_export_embeddings_command.py), then read [`references/workflows.md`](references/workflows.md#export-embeddings).
- **Cluster faces**: use [`scripts/build_cluster_command.py`](scripts/build_cluster_command.py), then read [`references/workflows.md`](references/workflows.md#cluster-faces).
- **Contributed examples**: read [`references/contributed-workflows.md`](references/contributed-workflows.md) before using contributed webcam, prediction, or Chinese-whispers code.

## Key runtime facts

- The embedding tensor is `embeddings:0`; image input is `input:0`; inference uses `phase_train:0` set to `False`.
- `facenet.load_data(paths, False, False, image_size)` loads already-aligned images and prewhitens by default.
- `compare` aligns each input image using MTCNN before model inference.
- `classifier` trains a linear `sklearn.svm.SVC(kernel='linear', probability=True)` over embeddings and stores `(model, class_names)` in a pickle.
- Contributed export and clustering scripts overlap with core workflows but have additional assumptions and older APIs.

## Output contract

- Compare emits a human-readable distance matrix; save stdout with the model/preprocessing settings if it will be used as evidence.
- Classifier training writes a pickle containing the fitted SVM and class names; keep it paired with the exact identity-folder mapping used for training.
- Export writes embeddings and labels with matching row order; preserve the label-string array when handing outputs to another model.
- Clustering writes images under the requested output directory; use a temporary directory and record the threshold/minimum cluster size.

## Validation

Use command builders with `--help` first. Run full model-backed commands only after model/data paths are available. For automation, treat model downloads, raw webcam capture, and large folder clustering as user-approved operations, not default smoke tests.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for classifier pickle mismatches, no detected face, empty embedding arrays, old SciPy image I/O, sklearn label issues, and contributed script hazards.
