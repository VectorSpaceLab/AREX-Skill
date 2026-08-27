# Contributed workflow notes

The `contributed` directory contains useful examples, but several are less maintained than the core `src` scripts. Treat them as workflow evidence and adapt them carefully.

## `export_embeddings.py`

Best contributed script for exporting embeddings and labels as NumPy arrays. It overlaps with `classifier` feature extraction but is useful for downstream clustering, custom classifiers, or analysis.

Cautions:

- `--is_aligned` is declared as a string argument but compared to `True` in the script; command-line string values may not behave as expected without patching.
- Unaligned mode uses MTCNN and assumes at least one face per image.

## `batch_represent.py`

Also exports embeddings from a class-folder dataset and saves `gallery.npy` plus `signatures.npy`. It manually injects a source-relative path into `sys.path`, so prefer the exported command pattern from this skill instead of copying the script unchanged.

## `cluster.py`

Runs MTCNN alignment, Facenet embedding inference, and DBSCAN clustering over a folder of images. It writes cluster directories and optionally only the largest cluster. It is useful when the user needs grouping without a fixed number of clusters.

## `clustering.py`

Implements cosine-like encoding comparison and Chinese-whispers clustering. It uses older NetworkX API patterns such as `G.node`, so verify/patch NetworkX compatibility before running it in a modern environment.

## `predict.py`

Detects all faces in specified images, computes embeddings, loads an SVM classifier pickle, and prints predicted class probabilities. The source file has indentation/style issues in parts of the main loop, so treat it as a recipe rather than a stable script unless tested.

## `face.py` and `real_time_face_recognition.py`

Provide a high-level `Recognition` container and webcam loop. They are not safe default automation targets because they include hard-coded model/classifier paths, require camera/display access, and run a loop until the user presses `q`.

For production usage, parameterize checkpoint and classifier paths before using this code and avoid hard-coded repository-relative `model_checkpoints` paths.
