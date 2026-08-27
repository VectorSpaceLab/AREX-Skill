# Embeddings and classification troubleshooting

## No face detected during compare or clustering

The compare/cluster workflows remove or skip images when MTCNN finds no face. Check image quality, face size, occlusion, and whether the image is read as RGB. For bulk data, run alignment first and inspect the bounding-box log.

## Empty or tiny classifier dataset

`classifier` expects at least one image per class and may need many images if `--use_split_dataset` is enabled. Validate the dataset first and lower split thresholds only when scientifically appropriate.

## Classifier pickle does not match classes

The classifier pickle stores an SVM model and `class_names` from training time. If DATA_DIR classes changed after training, predictions may still print old class names. Retrain the classifier when identity folders or labels change.

## `ValueError` from `np.stack` or empty image list

Likely causes: no valid images, all images skipped by MTCNN, or a path pattern points at an empty directory. Validate file paths and test a small subset.

## `scipy.misc` image read/resize failures

Use an older compatible SciPy stack or patch image I/O to Pillow/OpenCV. This is common in contributed scripts and `compare` on modern Python environments.

## Memory errors during embedding export

Reduce `--batch_size` or `--image_batch`. `export_embeddings.py` stores the full embeddings array in memory; for very large datasets, shard by identity or directory and merge outputs explicitly.

## Webcam workflow hangs or opens no window

`real_time_face_recognition.py` requires camera device access and a display. It is not a headless smoke test. Use still-image `predict` or `compare` workflows for server environments.
