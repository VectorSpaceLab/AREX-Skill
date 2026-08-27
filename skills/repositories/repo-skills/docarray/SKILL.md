---
name: docarray
description: "Use DocArray for multimodal Pydantic-style documents, typed
  DocList and DocVec batches, serialization and local storage, FastAPI payloads,
  and vector retrieval indexes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DocArray

Use this repo skill when a task names DocArray or asks for a Python data model for multimodal records, typed document batches, document serialization, local document storage, FastAPI document payloads, or vector-index retrieval.

## Verified baseline

The verified default is a CPU workflow using DocArray base dependencies plus the `proto`, `pandas`, and `web` extras. Install the public package for normal use:

```bash
pip install -U docarray
# add only the surfaces you need:
pip install -U "docarray[proto,pandas,web]"
python -c "import docarray; print(docarray.__version__)"
```

For the current verified `DocVec` path, prefer `numpy<2` and run the bundled smoke helpers before trusting a new environment. Optional tensor frameworks, media loaders, cloud stores, and external vector databases are not implied by the base install.

## Route by task

- **Model a record or multimodal schema**: read [`document-modeling`](sub-skills/document-modeling/SKILL.md) for `BaseDoc`, predefined modality docs, dynamic schemas, `DocList`, `DocVec`, nested fields, and typed tensor shapes.
- **Serialize, store, stream, or serve documents**: read [`serialization-storage`](sub-skills/serialization-storage/SKILL.md) for JSON, protobuf, bytes, base64, binary files, CSV/DataFrame exchange, `file://`, S3 boundaries, and `DocArrayResponse`.
- **Index, search, filter, or persist vectors**: read [`vector-indexing`](sub-skills/vector-indexing/SKILL.md) for `InMemoryExactNNIndex`, query builders, subindexes, persistence, and optional backend selection.

Tasks that span multiple surfaces should start here, choose the schema in `document-modeling`, then hand the resulting typed documents to `serialization-storage` or `vector-indexing`.

## Fast decisions

| Need | First choice | Watch for |
| --- | --- | --- |
| One validated data point | `BaseDoc` subclass | Required fields, nested docs, and per-document tensor shapes. |
| Mutable/reorderable/streaming collection | `DocList[MyDoc]` | Typed lists are homogeneous; bare `DocList` may be heterogeneous. |
| Contiguous ML batch | `DocVec[MyDoc]` | Homogeneous fields; optional doc/tensor columns must be all present or all missing. |
| Human-readable transport | JSON | Rich tensor/list unions may need explicit schema handling. |
| Compact trusted transport | protobuf or protobuf-array | Install `docarray[proto]`; document unions are not protobuf-safe. |
| Local retrieval prototype | `InMemoryExactNNIndex[MyDoc]` | Dimensioned vector field and backend-specific filter/query behavior. |
| Production/vector service | Optional backend | Install and verify the chosen client, service, credentials, schema, and metric separately. |

## Common failure boundaries

- Missing `google.protobuf`, `pandas`, `fastapi`, or backend client: install the matching narrow extra; do not install `full` by default.
- `DocVec` fails with a NumPy `device` error: check NumPy compatibility and try `numpy<2` for the current verified CPU path.
- File-store push raises `FileNotFoundError`: create the explicit parent namespace directory first.
- CSV cannot rebuild tensor fields: use JSON, protobuf-array, binary, or DataFrame instead; CSV is safest for scalar rows.
- In-memory query builder does not support text search, and equal-score result ties can expose a comparison edge case; see the vector troubleshooting reference.

Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting recovery guidance and [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a changed checkout.

## Routing metadata path convention

In `references/repo-routing-metadata.json`, every `useful_entry_points` value is a path relative to this DocArray skill root (the directory containing this `SKILL.md`), not a repository- or bundle-prefixed path.

## Safe bundled checks

These helpers are self-contained and do not require the original repository checkout:

```bash
python sub-skills/document-modeling/scripts/schema_smoke.py --help
python sub-skills/serialization-storage/scripts/roundtrip_smoke.py --help
python sub-skills/vector-indexing/scripts/inmemory_index_smoke.py --help
python scripts/check_env.py --help
```

Run the relevant helper after installing the package and selected extras. Helpers use tiny in-memory or temporary-file fixtures; they do not start databases, use credentials, or download models.

## Public capability boundaries

DocArray also exposes Torch, TensorFlow, JAX, image/audio/video/mesh loaders, S3, HNSWLib, Qdrant, Weaviate, Elasticsearch, Redis, Milvus, MongoDB Atlas, Epsilla, and Jina/FastAPI integrations. Those are routed by the sub-skills but remain optional until their exact dependency variant, service/network/credential plan, and native smoke have been verified.
