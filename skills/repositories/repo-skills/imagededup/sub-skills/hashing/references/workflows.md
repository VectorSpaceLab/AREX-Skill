# Hashing workflows

## 1. Generate a hash for one image

Use a hash class directly:

```python
from imagededup.methods import PHash

phasher = PHash()
hash_string = phasher.encode_image(image_file='path/to/image.jpg')
```

Use `image_array=` when you already have a numpy array.

## 2. Generate hashes for a directory

```python
from imagededup.methods import DHash

dhasher = DHash()
encoding_map = dhasher.encode_images(image_dir='path/to/images', recursive=False)
```

Use `recursive=True` when you want nested images included.

## 3. Find duplicates from a directory

```python
from imagededup.methods import PHash

phasher = PHash()
duplicate_map = phasher.find_duplicates(
    image_dir='path/to/images',
    max_distance_threshold=10,
    scores=False,
)
```

Key decisions:

- Use `scores=True` if you want the Hamming distance next to each duplicate.
- Use `outfile='results.json'` if you want the map persisted.
- Use a lower threshold to be stricter.

## 4. Find duplicates from precomputed hashes

If you already have encodings, skip image reloading:

```python
duplicate_map = phasher.find_duplicates(
    encoding_map=encoding_map,
    max_distance_threshold=10,
    scores=True,
)
```

This is useful when encoding is expensive or you want to compare search backends separately from encoding.

## 5. Produce a removal list

```python
remove_list = phasher.find_duplicates_to_remove(
    image_dir='path/to/images',
    max_distance_threshold=10,
)
```

This is a heuristic list. It is intentionally not a file deletion tool.

## 6. Choose a search backend

- `brute_force_cython`: default on Unix-like systems.
- `bktree`: default on Windows.
- `brute_force`: pure-Python comparison helper when you want a simpler backend.

Choose the backend only when you are debugging search behavior or comparing correctness/performance.

## 7. Compare hash families

- `PHash`: perceptual and transform-tolerant.
- `AHash`: simple and fast.
- `DHash`: fast difference-based filter.
- `WHash`: wavelet-based option for a different transform bias.

## 8. Validation workflow

Before searching, confirm:

1. the directory exists
2. the image set is the one you think it is
3. the threshold type matches the method
4. the encoding map is symmetric if you are passing one manually
5. on Windows, the runnable script is wrapped in a main guard

## 9. Recommended smoke flow

Use the bundled smoke script when you want a quick check without repo fixtures:

```bash
python scripts/hash_smoke.py
```

That script creates a tiny synthetic image directory, runs encoding, duplicate search, and removal-list generation, and prints a JSON summary.