# Embedding and classification workflows

## Compare images

The Facenet `compare` workflow detects and aligns one face per input image, loads a trained model, computes embeddings, and prints a pairwise Euclidean distance matrix.

Build a command:

```bash
python scripts/build_compare_command.py MODEL_PATH image1.jpg image2.jpg --image-size 160 --margin 44
```

Then execute the emitted command in a Facenet environment. Use at least two image files. If any image has no detected face, the source workflow removes that image from the batch and prints a warning.

## Train or use an SVM classifier

The `classifier` workflow has two modes:

- `TRAIN`: compute embeddings for all class-folder images and save a pickle containing `(model, class_names)`.
- `CLASSIFY`: compute embeddings for test images and print predicted class probabilities plus accuracy.

Build training command:

```bash
python scripts/build_classifier_command.py TRAIN ALIGNED_DATA_DIR MODEL_PATH classifier.pkl --batch-size 90
```

Build classification command:

```bash
python scripts/build_classifier_command.py CLASSIFY TEST_DATA_DIR MODEL_PATH classifier.pkl --batch-size 90
```

Important details:

- The classifier is `sklearn.svm.SVC(kernel='linear', probability=True)`.
- Class names are derived from sorted Facenet dataset classes and underscores are replaced with spaces when saved.
- `--use_split_dataset` splits one dataset into train/test subsets, but defaults require at least 20 images per class and 10 training images per class.
- The source script contains an assertion written as `assert(condition, message)`, which Python treats as an always-true tuple assertion warning. Validate non-empty classes separately before trusting a run.

## Export embeddings

`contributed/export_embeddings.py` exports three `.npy` files:

- embeddings array, default `embeddings.npy`
- integer labels array, default `labels.npy`
- label strings aligned to each row, default `label_strings.npy`

Build a command:

```bash
python scripts/build_export_embeddings_command.py MODEL_DIR ALIGNED_DATA_DIR --image-batch 500 --embeddings-name embeddings.npy
```

For already aligned datasets, leave `--is-aligned` true. For raw images, use the alignment sub-skill first or explicitly enable unaligned handling only after checking detector assumptions.

## Cluster faces

`contributed/cluster.py` aligns images, computes embeddings, constructs a distance matrix, and runs DBSCAN with a precomputed metric. Build a command:

```bash
python scripts/build_cluster_command.py MODEL_PATH IMAGE_DIR OUT_DIR --cluster-threshold 1.0 --min-cluster-size 1
```

Use `--largest-cluster-only` when the task is filtering for the dominant identity. Use a temporary output directory because cluster workflows write copied/cropped image files.

## Choosing thresholds

The repository prints squared/Euclidean-like distances depending on workflow internals. Do not invent an identity threshold without calibration. Prefer LFW-style evaluation or a labeled validation split for a new dataset.

## Validation checklist

- Model path loads as a checkpoint directory or frozen graph.
- Dataset is aligned and class-folder structured when needed.
- `phase_train:0` is fed `False` for inference.
- Batch size divides or bounds available memory.
- Output pickle/`.npy`/cluster directory paths are writable.
