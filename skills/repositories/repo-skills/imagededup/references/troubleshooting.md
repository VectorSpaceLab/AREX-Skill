# Cross-cutting troubleshooting

## Import and install failures

### Symptom: `ModuleNotFoundError: numpy` or `ModuleNotFoundError: scipy`

- Cause: the repo metadata under-declares runtime dependencies.
- Fix: install `numpy` and `scipy` explicitly before or with the package.

### Symptom: editable install fails while building the Cython extension

- Cause: the environment does not have the build toolchain or `cython` yet.
- Fix: install `cython` and retry the editable install.
- If the local build still fails, inspect the generated extension build log rather than assuming the package import is broken.

### Symptom: `CNN()` fails on first use

- Cause: missing `torch` / `torchvision`, a broken model cache, or blocked access to pretrained weights.
- Fix: confirm `torch` and `torchvision` import cleanly, then retry with network access or a warm cache.
- If you only need a custom-model workflow, use `CustomModel` and a lightweight model instead of the pretrained backbone.

## Backend and platform issues

### Symptom: `CNN()` selects CPU when you expected CUDA

- Cause: `torch.cuda.is_available()` is false in the active environment, or the installed torch build does not expose CUDA.
- Fix: inspect the environment's torch build and GPU visibility before assuming the CNN path is GPU-capable.
- On CUDA hosts, `CNN()` should report `cuda` and can run duplicate search there.

### Symptom: multiprocessing errors on Windows

- Cause: hash workflows use multiprocessing and the script was not guarded with a main entry point.
- Fix: wrap runnable code in `if __name__ == '__main__':` before starting image encoding or duplicate search.

### Symptom: `num_enc_workers` seems ignored

- Cause: the CNN path only parallelizes image encoding on Linux, and the hash workflows may warn when encodings are already provided.
- Fix: treat worker-count arguments as platform- and workflow-specific. Read the warning message rather than forcing a worker count into every path.

## Data and API validation issues

### Symptom: `Please provide a valid directory path!`

- Cause: `image_dir` is not a directory.
- Fix: pass the directory path, not a file path, to `encode_images` or directory-based duplicate search.

### Symptom: `Please provide either image file path or image array!`

- Cause: `encode_image` received the wrong input type.
- Fix: supply either a real file path or a numpy image array.

### Symptom: `Threshold must be an int between 0 and 64`

- Cause: a hash threshold was given as the wrong type or outside range.
- Fix: use an integer in the inclusive range `0..64`.

### Symptom: `Threshold must be a float between -1.0 and 1.0`

- Cause: a CNN similarity threshold is not a float in range.
- Fix: use a float between `-1.0` and `1.0`.

### Symptom: `Provide either an image directory or encodings!`

- Cause: `find_duplicates` or `find_duplicates_to_remove` was called without a valid `image_dir` or `encoding_map`.
- Fix: choose one input path and supply it consistently.

### Symptom: `recursive parameter is irrelevant when using encodings.`

- Cause: `encoding_map` was passed with `recursive=True`.
- Fix: remove the recursive flag for encoding-map workflows.

### Symptom: `Parameter num_enc_workers has no effect since encodings are already provided`

- Cause: worker count was supplied while using a precomputed encoding map.
- Fix: ignore that parameter for encoding-map workflows.

## Evaluation and plotting issues

### Symptom: `Please ensure that ground truth and retrieved map have the same keys!`

- Cause: evaluation input maps do not cover the same images.
- Fix: make the key sets identical before calling `evaluate`.

### Symptom: symmetric relationships fail validation

- Cause: a map says `A` duplicates `B` but the reverse is missing.
- Fix: mirror duplicate relationships on both sides for both ground truth and retrieved maps.

### Symptom: `Provided filename has no duplicates!`

- Cause: `plot_duplicates` was asked to plot an image whose duplicate list is empty.
- Fix: choose a key with at least one duplicate or inspect the duplicate map first.

### Symptom: sklearn warns that precision is ill-defined

- Cause: tiny synthetic evaluation examples may not contain predicted samples for every class.
- Fix: treat the warning as expected on toy fixtures; use a richer example if you want stable per-class metrics.

## Workflow-specific gotchas

- `find_duplicates_to_remove` uses a heuristic and may return either member of a duplicate pair depending on traversal order and retention logic.
- Hashing outputs are strings; CNN outputs are feature arrays.
- The default CNN backbone may download weights the first time it is instantiated.
- Keep plot commands on an Agg backend or in a noninteractive environment when running headless.