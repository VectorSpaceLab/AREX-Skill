# CNN workflows

## 1. Use the default pretrained CNN workflow

```python
from imagededup.methods import CNN

cnn = CNN()
encodings = cnn.encode_images(image_dir='path/to/images')
duplicate_map = cnn.find_duplicates(encoding_map=encodings)
```

What to remember:

- `CNN()` selects CUDA when it is available.
- The default backbone is MobileNetV3 Small.
- The first instantiation may download weights if they are not cached.

## 2. Use a custom PyTorch model

```python
from imagededup.methods import CNN
from imagededup.utils import CustomModel
```

Then provide:

- a model object
- a transform that matches the model's preprocessing
- a readable name for the model

The model should return one feature vector per image.

## 3. Encode a single image

```python
encoding = cnn.encode_image(image_file='path/to/image.jpg')
```

Use `image_array=` when you already have a numpy array.

## 4. Encode a directory

```python
encodings = cnn.encode_images(image_dir='path/to/images', recursive=False)
```

Notes:

- directory values are numpy arrays, not strings
- corrupted images are skipped
- `recursive=True` includes nested images

## 5. Find duplicates

```python
duplicate_map = cnn.find_duplicates(
    encoding_map=encodings,
    min_similarity_threshold=0.9,
    scores=True,
)
```

Important choices:

- use `scores=True` when you want the cosine similarity next to each duplicate
- use a higher threshold for stricter matching
- use `encoding_map` if the feature vectors were already computed earlier

## 6. Produce a removal list

```python
remove_list = cnn.find_duplicates_to_remove(encoding_map=encodings)
```

This is a heuristic list, not a file deletion tool.

## 7. Suggested validation sequence

1. Verify the model and transform agree on input shape.
2. Encode a single image.
3. Encode a small directory.
4. Run duplicate search from the encoding map.
5. Only then compare or plot duplicate results.

## 8. Recommended smoke flow

Use the bundled smoke script when you want to exercise the workflow without repo fixtures:

```bash
python scripts/cnn_smoke.py --mode custom
```

Use `--mode pretrained` only when you want to confirm the default backbone path and you are comfortable with the first-use weight download.

## 9. GPU/CPU guidance

- CUDA is helpful but not required.
- CPU fallback is a valid supported path.
- Do not treat a CPU-only installation as proof that a broken CUDA setup is healthy.