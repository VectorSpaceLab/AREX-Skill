# Embedding/classification CLI reference

## Compare

Command shape:

```bash
python -m compare MODEL IMAGE [IMAGE ...] --image_size 160 --margin 44 --gpu_memory_fraction 1.0
```

Inputs:

- `MODEL`: checkpoint directory or frozen `.pb` graph.
- `IMAGE`: one or more raw image files; MTCNN alignment is performed internally.

Output: image index list plus a distance matrix.

## Classifier

Command shape:

```bash
python -m classifier TRAIN DATA_DIR MODEL CLASSIFIER.pkl --batch_size 90 --image_size 160
python -m classifier CLASSIFY DATA_DIR MODEL CLASSIFIER.pkl --batch_size 90 --image_size 160
```

Optional split flags:

- `--use_split_dataset`
- `--min_nrof_images_per_class` default `20`
- `--nrof_train_images_per_class` default `10`

Output:

- `TRAIN` saves a pickle classifier.
- `CLASSIFY` prints per-image class probabilities and overall accuracy.

## Export embeddings

Command shape:

```bash
python -m export_embeddings MODEL_DIR DATA_DIR --is_aligned True --image_batch 500 --embeddings_name embeddings.npy --labels_name labels.npy --labels_strings_name label_strings.npy
```

The contributed script expects importable Facenet and contributed modules. Prefer aligned data unless the user explicitly wants per-image MTCNN alignment.

## DBSCAN cluster

Command shape:

```bash
python -m cluster MODEL DATA_DIR OUT_DIR --image_size 160 --margin 44 --min_cluster_size 1 --cluster_threshold 1.0
```

The script writes images into cluster-numbered directories under `OUT_DIR`; use temporary or explicitly approved output directories.
