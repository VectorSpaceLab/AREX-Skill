---
name: document-modeling
description: "Model multimodal data with DocArray BaseDoc schemas, predefined
  documents, DocList, DocVec, nested fields, and typed tensors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DocArray document modeling

Use this sub-skill when a task needs to define, validate, or batch multimodal DocArray data models.

## Route here for

- Designing `BaseDoc` schemas for text, image, audio, video, embeddings, metadata, and nested multimodal payloads.
- Choosing predefined document classes such as `TextDoc` and `ImageDoc` versus custom `BaseDoc` subclasses.
- Creating dynamic document classes with `create_doc()` or `create_doc_from_dict()`.
- Choosing `DocList` versus `DocVec` for streaming, reranking, shuffling, or contiguous ML batch processing.
- Modeling nested documents, nested `DocList` fields, optional fields, and shape-checked `NdArray` tensor fields.
- Handling optional Torch, TensorFlow, or JAX tensor type boundaries without claiming those optional backends are verified.

## Route elsewhere

- Serialization protocols, protobuf/JSON/bytes/CSV/DataFrame round-trips, file stores, S3, or FastAPI response payloads: use sibling [`serialization-storage`](../serialization-storage/).
- Vector indexes, nearest-neighbor search, document indexes, or external vector database backends: use sibling [`vector-indexing`](../vector-indexing/).

## Read these bundled references

1. Start with [API reference](references/api-reference.md) for verified imports, constructor signatures, core class behavior, and the modeling decision table.
2. Use [Workflows](references/workflows.md) for task recipes and copyable examples.
3. Use [Troubleshooting](references/troubleshooting.md) when validation, Pydantic config, `DocList`, `DocVec`, NumPy, or optional tensor backends fail.

## Safe bundled helper

Run [schema_smoke.py](scripts/schema_smoke.py) in an environment where DocArray is installed to confirm the main schema, dynamic document, `DocList`, typed tensor, and optional `DocVec` paths:

Run these commands from this sub-skill root (the directory containing this `SKILL.md`):

```bash
python scripts/schema_smoke.py --help
python scripts/schema_smoke.py
python scripts/schema_smoke.py --skip-docvec
```

The verified minimum scope is CPU with DocArray base plus proto, pandas, and web extras. Optional services and tensor frameworks are documented as boundaries, not verified defaults.
