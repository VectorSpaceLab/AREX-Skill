# CNN API reference

## Public classes

### `CNN`

Main duplicate-search class for CNN features.

Important constructor behavior:

- `CNN(verbose=True, model_config=None)`
- if `model_config` is omitted, the default pretrained `MobilenetV3` wrapper is used
- the selected device is CUDA when available, otherwise CPU
- the object keeps the chosen model, transform, and device on the instance

### `CustomModel`

A small named-tuple wrapper that carries:

- `name`
- `model`
- `transform`

Use it to plug a user-defined PyTorch model into `CNN`.

### Pretrained wrapper models

- `MobilenetV3`: default wrapper; output feature size is `576`
- `ViT`: output feature size is `768`
- `EfficientNet`: output feature size is `1792`

These wrappers already provide a matching transform and a stable name.

## Main methods

### `encode_image(image_file=None, image_array=None)`

- Returns a numpy array of shape `(1, features)`.
- Accepts either a file path or a numpy image array.
- Grayscale arrays are expanded to RGB-compatible arrays before preprocessing.
- Invalid input types raise `ValueError`.

### `encode_images(image_dir, recursive=False, num_enc_workers=0)`

- Returns a dictionary mapping relative filenames to CNN feature arrays.
- Uses a DataLoader and batches images.
- Skips unreadable files rather than failing the entire batch.
- `num_enc_workers` is only honored on Linux; other platforms coerce it to `0`.

### `find_duplicates(image_dir=None, encoding_map=None, min_similarity_threshold=0.9, scores=False, outfile=None, recursive=False, num_enc_workers=0, num_sim_workers=cpu_count())`

- Returns a duplicate map keyed by filename.
- Uses cosine similarity instead of Hamming distance.
- When `scores=True`, the values are `(duplicate_filename, similarity)` tuples.
- If you provide `encoding_map`, the directory-only flags become irrelevant.

### `find_duplicates_to_remove(...)`

- Returns one heuristic list of filenames to remove.
- Never deletes files.
- The returned list is derived from the duplicate map.

## Model configuration rules

- `model_config.model` must be a PyTorch module or call-compatible object.
- `model_config.transform` must turn a PIL image into the tensor expected by the model.
- If the wrapper name stays at the default name, the code emits a warning encouraging a custom name.
- A custom model should preserve the batch dimension and return one feature vector per image.

## Threshold and output rules

- CNN thresholds are floats in the range `-1.0..1.0`.
- Higher is stricter.
- Duplicate tuples are sorted by similarity logic inside the search backend.
- The returned encoding map values are numpy arrays, not hex strings.

## Internal support objects worth knowing about

- `img_dataloader`: builds the batched image loader.
- `expand_image_array_cnn`: turns grayscale arrays into 3-channel arrays.
- `load_image` and `preprocess_image`: shared image handling helpers.

## When to read this file

Read this file when you need exact constructor behavior, feature sizes, custom model rules, or the CUDA-versus-CPU path for CNN duplicate detection.