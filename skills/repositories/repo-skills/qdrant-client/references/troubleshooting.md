# Cross-Cutting Troubleshooting

Read this when a qdrant-client task fails before it clearly belongs to one sub-skill.

## Install Or Import Fails

- Symptom: `ModuleNotFoundError: No module named 'qdrant_client'`.
  - Install `qdrant-client` into the Python environment that runs the code.
  - Verify with `python -c "from qdrant_client import QdrantClient, models; print(QdrantClient, models.VectorParams)"`.
- Symptom: imports fail for `numpy`, `httpx`, `grpc`, `pydantic`, `protobuf`, `portalocker`, or `urllib3`.
  - Reinstall the base package so its runtime dependencies are present.
  - Run `python -m pip check` to catch dependency conflicts.
- Symptom: inference code fails for `fastembed`.
  - Install exactly one optional extra: `qdrant-client[fastembed]` or `qdrant-client[fastembed-gpu]`.
  - Do not install CPU and GPU FastEmbed extras in the same environment.

## No Server Or Wrong Mode

- Symptom: connection refused, timeout, or server-version warnings.
  - Use `QdrantClient(":memory:")` for no-server examples.
  - Use `connection-and-transport` when a real server or Cloud cluster is required.
  - Use `check_compatibility=False` only for constructor/config validation that should not contact a server.
- Symptom: raw `client.http`, `client.grpc_points`, or `client.grpc_collections` is unavailable.
  - Raw REST/gRPC clients exist only for remote clients, not local mode.

## Constructor Confusion

- Pass only one of `location`, `url`, `host`, or `path`.
- Use `url` for complete endpoints and Qdrant Cloud URLs.
- Use `host` without `http://` or `https://`; use `url` when the protocol is part of the value.
- Put a reverse-proxy path either in `url` or `prefix`, not both.

## Data And Model Mismatch

- Vector dimensions in `models.VectorParams(size=...)` must match point vectors and query vectors.
- Named vectors require a matching `using` value or a query vector object that identifies the vector name.
- Sparse vectors need equal-length `indices` and `values` lists.
- Payload filters use exact field paths and strict model field names; route schema issues to `models-and-conversions`.

## Safe Validation

Run the shared smoke helper after installation:

```bash
python path/to/qdrant-client/scripts/qdrant_client_smoke.py --mode local
```

Use sub-skill helpers for narrower diagnostics: transport constructor probing, local persistence, async lifecycle, inference optional dependencies, upload shape checks, and conversion examples.
