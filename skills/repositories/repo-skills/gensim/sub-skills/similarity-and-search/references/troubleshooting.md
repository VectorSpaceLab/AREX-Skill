# Similarity and Search Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| All similarity scores are zero or near zero | Query vector is empty or in the wrong vector space. | Re-tokenize with the saved dictionary and transform through the same model chain used for indexing. |
| Shape or `num_features` errors | Index dimension does not match transformed vector ids. | Set `num_features` to the correct feature count or latent dimension; rebuild the index after changing transforms. |
| Memory exhaustion with `MatrixSimilarity` | Dense matrix does not fit RAM. | Use `SparseMatrixSimilarity` for sparse vectors or `Similarity` for sharded on-disk indexing. |
| Saved sharded index fails to load or query | Missing shard sidecar files or moved output prefix. | Keep all generated shard/index files together and save/load from a stable location. |
| `ImportError: Annoy not installed` | Optional Annoy dependency missing. | Install `annoy` or use exact Gensim indexes. |
| `ImportError: NMSLIB not installed` | Optional NMSLIB dependency missing or unsupported for Python/platform. | Install a compatible `nmslib` wheel if available, or use exact/Annoy alternatives. |
| WMD fails with `ot`/POT missing | Optional optimal transport dependency missing. | Install POT only when WMD is required; otherwise use cosine/soft-cosine alternatives. |
| WMD or soft cosine is too slow | Pairwise term/document computations are expensive. | Limit vocabulary, reduce candidate set, use exact cosine first, or cache term similarity matrices. |
| Result ids cannot be mapped to documents | No external document-id map was stored. | Persist an index-position-to-document metadata table next to the index. |

## Diagnostic checklist

1. Print the query tokens and BoW vector.
2. Confirm the query went through every transform used by the corpus.
3. Check vector dimensions and `num_features`.
4. Run `scripts/similarity_query_smoke.py` on an embedded fixture.
5. Probe optional imports only for the optional metric/index actually requested.
