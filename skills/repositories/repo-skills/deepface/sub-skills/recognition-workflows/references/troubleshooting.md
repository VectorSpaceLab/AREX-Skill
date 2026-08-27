# Recognition Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `embeddings of Facenet should have 128 dimensions` | Precomputed embeddings came from a different model than `model_name`. | Use the model that produced the embeddings or recompute embeddings. |
| `When passing img1_path as a list... type float` | Nested list, strings, or malformed embedding passed to `verify`. | Pass a flat numeric vector or an image input. |
| `Source and target embeddings must have same dimensions` during `find` | Local datastore pickle was built with a different model/version/settings. | Rebuild the datastore after user approval; keep model, detector, alignment, normalization, and expansion consistent. |
| Signed datastore complains about credentials or signature | A `.ldsa` signature exists and cannot be verified. | Provide matching LightDSA credentials or recreate from trusted images after approval. |
| `No item found in <db_path>` | Local image folder has no valid JPEG/PNG files. | Validate folder contents; non-JPEG/PNG files and mislabeled formats are skipped. |
| Encrypted embedding missing | Embedding contained negative values or was not L2-normalized. | Set `minmax_normalize=True` and `l2_normalize=True` where suitable before passing `cryptosystem`. |
