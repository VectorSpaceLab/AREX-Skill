# Recognition Workflows

## Verify Two Face Images

```python
from deepface import DeepFace
result = DeepFace.verify("alice_1.jpg", "alice_2.jpg", model_name="VGG-Face", detector_backend="opencv", distance_metric="cosine")
print(result["verified"], result["distance"], result["threshold"], result["confidence"])
```

Use `threshold=` only when the user has a domain-specific operating point. Keep the reported default threshold in logs so the override is auditable.

## Generate Embeddings

```python
embedding_objs = DeepFace.represent("alice.jpg", model_name="Facenet", detector_backend="opencv", max_faces=1)
embedding = embedding_objs[0]["embedding"]
```

For batch inputs, pass a list of image paths or a 4D NumPy array. The return becomes a list of per-input lists.

## Verify Precomputed Embeddings

```python
result = DeepFace.verify(img1_path=embedding_a, img2_path=embedding_b, model_name="Facenet", silent=True)
```

The embeddings must be flat numeric lists from the same model. If dimensions do not match, rerun representation with the correct `model_name` or change the verify model to match the stored embedding length.

## Search A Local Folder

```python
dfs = DeepFace.find("query.jpg", db_path="known_faces", model_name="VGG-Face", detector_backend="opencv", refresh_database=True, silent=True)
```

The first run builds a datastore pickle in the image folder. Later runs update it by default. Use `refresh_database=False` only when the user intentionally wants to ignore directory changes.

## Similarity Search / Look-Alikes

```python
lookalikes = DeepFace.find("query.jpg", db_path="known_faces", similarity_search=True, k=10, silent=True)
```

With `similarity_search=True`, results can include faces beyond the verification threshold. Treat them as nearest neighbors, not confirmed identities.

## Compare Embeddings Without Building Models

Use the bundled helper when the user already has JSON arrays:

```bash
python sub-skills/recognition-workflows/scripts/deepface_embedding_distance.py --embedding-a a.json --embedding-b b.json --metric cosine --model VGG-Face
```
