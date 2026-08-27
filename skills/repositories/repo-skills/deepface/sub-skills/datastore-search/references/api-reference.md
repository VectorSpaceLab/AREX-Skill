# Datastore Search API Reference

## `DeepFace.register`

```python
DeepFace.register(img, img_name=None, model_name="VGG-Face", detector_backend="opencv", enforce_detection=True, align=True, l2_normalize=False, expand_percentage=0, normalization="base", anti_spoofing=False, database_type="postgres", connection_details=None, connection=None) -> dict
```

Returns `{"inserted": <count>}`. `img_name` is stored as the identity label; if omitted, DeepFace derives a name from an image path or generates an identifier.

## `DeepFace.search`

```python
DeepFace.search(img, model_name="VGG-Face", detector_backend="opencv", distance_metric="cosine", enforce_detection=True, align=True, l2_normalize=False, expand_percentage=0, normalization="base", anti_spoofing=False, similarity_search=False, k=None, database_type="postgres", connection_details=None, connection=None, search_method="exact") -> list[pandas.DataFrame]
```

Search returns one DataFrame per detected source face. Columns include `id`, `img_name`, `model_name`, `detector_backend`, `aligned`, `l2_normalized`, `search_method`, target box coordinates, `threshold`, `distance_metric`, `distance`, and `confidence`.

## `DeepFace.build_index`

Use `DeepFace.build_index(...)` before `search_method="ann"` for non-vector databases. Vector databases manage their own indexes and may no-op or use service-native indexing.

## Exact Versus ANN

`search_method="exact"` fetches all matching embeddings and computes distances in Python. `search_method="ann"` on non-vector backends requires FAISS and a stored index. Vector DB backends use service-native nearest-neighbor search.
