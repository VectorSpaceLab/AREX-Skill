---
name: serialization-storage
description: "Serialize, persist, stream, and route DocArray BaseDoc, DocList,
  DocVec, file store, S3, and FastAPI payload workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DocArray serialization and storage

Use this sub-skill when a task needs to move DocArray objects across process, file, tabular, web, or object-store boundaries.

## Route here for

- Choosing JSON, protobuf, bytes, base64, binary file, CSV, or DataFrame formats for `BaseDoc`, `DocList`, and `DocVec`.
- Preserving or deliberately changing `DocVec` tensor backend with `tensor_type=...` during deserialization.
- Saving and loading `DocList` or `DocVec` binaries, including streaming-safe single-document protocols.
- Using `DocList.push()`, `DocList.pull()`, `push_stream()`, and `pull_stream()` with `file://` stores.
- Documenting S3 `DocList` store requirements and constraints before credentials or network access are available.
- Returning DocArray documents and JSON payloads from FastAPI with `DocArrayResponse`.
- Diagnosing missing `proto`, `pandas`, `web`, or `aws` extras and protocol mismatch failures.

## Route elsewhere

- Schema design, predefined documents, nested document modeling, and tensor field choices before serialization: use sibling [`document-modeling`](../document-modeling/).
- Vector indexes, nearest-neighbor search, document indexes, or vector database backends: use sibling [`vector-indexing`](../vector-indexing/).
- Live S3 operations that require credentials, buckets, endpoints, or network access: verify those separately in the future task before relying on them.

## Read these bundled references

1. Start with [Serialization reference](references/serialization-reference.md) for the protocol matrix, exact method names, `DocVec tensor_type` behavior, CSV/DataFrame caveats, and FastAPI response routing.
2. Use [Storage reference](references/storage-reference.md) for `file://` and S3 `DocList` store behavior, streaming, list/delete operations, path requirements, and optional service constraints.
3. Use [Troubleshooting](references/troubleshooting.md) when optional extras, protobuf unions, CSV tensor fields, file namespace paths, `local_cache`, S3 credentials, or FastAPI imports fail.

## Safe bundled helper

Run [roundtrip_smoke.py](scripts/roundtrip_smoke.py) in any environment where DocArray is installed to exercise safe local round-trips without external services:

Run these commands from this sub-skill root (the directory containing this `SKILL.md`):

```bash
python scripts/roundtrip_smoke.py --help
python scripts/roundtrip_smoke.py
python scripts/roundtrip_smoke.py --skip-protobuf --skip-dataframe --skip-file-store
```

The verified minimum scope is CPU with DocArray base plus `proto`, `pandas`, and `web` extras. Optional S3/AWS services and optional tensor frameworks are documented as boundaries, not verified defaults.
