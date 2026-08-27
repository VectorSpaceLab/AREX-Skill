# Cross-cutting DocArray troubleshooting

## Install the narrow extra

DocArray keeps many integrations optional and imports them lazily. Use the error's missing module to choose one extra:

| Missing module/surface | Install | Verify next |
| --- | --- | --- |
| `google.protobuf` or `lz4` | `pip install "docarray[proto]"` | `python -c "from docarray import DocList; print(DocList)"` and run the protobuf helper. |
| `pandas` | `pip install "docarray[pandas]"` | `python -c "import pandas; print(pandas.__version__)"` and run DataFrame smoke. |
| `fastapi` | `pip install "docarray[web]"` | `python -c "from docarray.base_doc import DocArrayResponse; print(DocArrayResponse)"`. |
| `smart_open`, `boto3`, `botocore` | `pip install "docarray[aws]"` | Configure credentials/endpoint separately; do not run a live S3 call as an import check. |
| an external index client | the selected backend extra | Verify the service, schema, dimensions, credentials, and a tiny index/find/delete cycle. |

Do not use `docarray[full]` as a first repair: it adds unrelated media and tensor/backend dependencies and can create version conflicts.

## Version and environment mismatch

- Confirm the interpreter with `python -c "import sys; print(sys.executable); print(sys.version)"`.
- Confirm the installed distribution with `python -m pip show docarray` and the import with `python -c "import docarray; print(docarray.__file__)"`.
- This record carries a snapshot/version drift warning: the observed package metadata is `0.41.0`, while the checked-in `docarray.__version__` constant is `0.40.2`. These are observations, not an authoritative version claim. Re-observe both from the same checkout during a refresh, retain the warning if they differ, and remove it only after the provenance reconciliation rule is satisfied.
- If a wheel and editable checkout disagree, isolate the environment and rerun the bundled smoke helpers.
- For the current verified `DocVec` NumPy path, use `numpy<2`; NumPy 2.x exposed a device-argument incompatibility in the in-tree NumPy backend during verification.

## Route the failure

- Schema, shape, nested-document, `DocList`, or `DocVec` issue: [`document-modeling`](../sub-skills/document-modeling/references/troubleshooting.md).
- Wire format, protocol, CSV/DataFrame, file store, S3, or FastAPI response issue: [`serialization-storage`](../sub-skills/serialization-storage/references/troubleshooting.md).
- Search field, dimensions, index schema, filter/query builder, persistence, or external vector service issue: [`vector-indexing`](../sub-skills/vector-indexing/references/troubleshooting.md).

## Safety boundaries

Do not unpickle untrusted payloads. Do not put credentials in generated code or logs. Do not start a database or cloud operation merely to prove that the base package imports. Preserve optional backend failures as unverified until the actual backend is exercised.
