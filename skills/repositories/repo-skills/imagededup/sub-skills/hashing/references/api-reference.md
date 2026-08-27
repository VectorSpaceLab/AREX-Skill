# Hashing API reference

## Public classes

### `Hashing`

Base class that supplies common image-loading, hash conversion, encoding, and duplicate-search helpers.

Key behaviors:

- accepts either `image_file` or `image_array` for single-image encoding
- uses a 64-bit hex hash representation for all hashing subclasses
- exposes `find_duplicates` and `find_duplicates_to_remove`
- validates Hamming thresholds as integers in the range `0..64`

### `PHash`

- default target size: `32x32`
- perceptual hash implementation based on a DCT transform
- suitable for near-duplicate lookup when you want robustness to modest transforms

### `AHash`

- default target size: `8x8`
- average-hash implementation
- simple and fast for coarse exact/near duplicate filtering

### `DHash`

- default target size: `9x8`
- difference-hash implementation
- often the fastest hash path for exact duplicate work

### `WHash`

- default target size: `256x256`
- wavelet-hash implementation using Haar wavelets

## Main methods

### `encode_image(image_file=None, image_array=None)`

- Returns a single hexadecimal string.
- Use one real file path or one numpy image array.
- Invalid input types raise `ValueError`.

### `encode_images(image_dir=None, recursive=False, num_enc_workers=cpu_count())`

- Returns a dictionary mapping relative filenames to hash strings.
- Skips unreadable images.
- If `recursive=True`, nested images are included.
- On Windows, remember the multiprocessing main-guard caveat from the root troubleshooting notes.

### `find_duplicates(image_dir=None, encoding_map=None, max_distance_threshold=10, scores=False, outfile=None, search_method=..., recursive=False, num_enc_workers=cpu_count(), num_dist_workers=cpu_count())`

- Returns a duplicate map keyed by image filename.
- When `scores=True`, the values are `(duplicate_filename, distance)` tuples.
- The default search method is `brute_force_cython` on Unix-like systems and `bktree` on Windows.
- `encoding_map` and `recursive` do not make sense together; the code warns when both are supplied.

### `find_duplicates_to_remove(...)`

- Returns one heuristic list of filenames to remove.
- Never deletes files.
- Can read from either an image directory or an existing encoding map.

## Internal search helpers worth knowing about

- `BruteForce`: simple Python scan.
- `BKTree`: tree-based Hamming search.
- `BruteForceCython`: compiled brute-force search helper.
- `HashEval`: orchestration layer that wraps the search backend and returns sorted duplicate tuples.

## Threshold and output rules

- Hash thresholds are integer Hamming distances.
- Lower is stricter.
- Duplicate tuples are sorted by distance in ascending order.
- Removal lists are heuristic, so do not assume a single fixed member of a duplicate pair will always be retained.

## Input handling

- File paths may be `str` or `Path`-like objects.
- Arrays must be 2D grayscale or 3D RGB-compatible arrays.
- Unsupported array dimensionality triggers a `ValueError`.
- Invalid images are ignored during directory workflows.

## When to read this file

Read this file when you need exact method signatures, return shapes, threshold rules, or the backend selection behavior for hash workflows.