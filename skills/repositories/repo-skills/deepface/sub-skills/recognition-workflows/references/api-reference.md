# Recognition API Reference

## `DeepFace.verify`

```python
DeepFace.verify(img1_path, img2_path, model_name="VGG-Face", detector_backend="opencv", distance_metric="cosine", enforce_detection=True, align=True, expand_percentage=0, normalization="base", silent=False, threshold=None, anti_spoofing=False) -> dict
```

Inputs may be image paths, URLs, base64 data URIs, NumPy arrays, binary file-like objects, or flat precomputed embedding lists. If embedding lists are used, their length must match the selected `model_name` output dimension. The result includes `verified`, `distance`, `threshold`, `confidence`, `model`, `detector_backend`, `similarity_metric`, `facial_areas`, and `time`.

## `DeepFace.represent`

```python
DeepFace.represent(img_path, model_name="VGG-Face", enforce_detection=True, detector_backend="opencv", align=True, expand_percentage=0, normalization="base", anti_spoofing=False, max_faces=None, l2_normalize=False, minmax_normalize=False, return_face=False, cryptosystem=None) -> list[dict] | list[list[dict]]
```

A single image returns a list of face dictionaries. A sequence or 4D NumPy batch returns one list per input image. Each face dictionary contains `embedding`, `facial_area`, and `face_confidence`; `face` is included only when `return_face=True`; `encrypted_embedding` is included only when a cryptosystem is provided and the embedding satisfies encryption prerequisites.

## `DeepFace.find`

```python
DeepFace.find(img_path, db_path, model_name="VGG-Face", distance_metric="cosine", enforce_detection=True, detector_backend="opencv", align=True, similarity_search=False, k=None, expand_percentage=0, threshold=None, normalization="base", silent=False, refresh_database=True, anti_spoofing=False, batched=False, credentials=None) -> list[pandas.DataFrame] | list[list[dict]]
```

`db_path` is a local image directory. DeepFace creates a pickle datastore named from model, detector, alignment, normalization, and expansion settings. With `batched=False`, each detected source face returns a DataFrame. With `batched=True`, each detected source face returns a list of dictionaries optimized for larger searches.

Supported distance metrics are `cosine`, `euclidean`, `euclidean_l2`, and `angular`. If `threshold` is omitted, DeepFace uses a model/metric pre-tuned threshold. `DeepFace.find(..., credentials=...)` can sign and verify the pickle datastore with LightDSA.
