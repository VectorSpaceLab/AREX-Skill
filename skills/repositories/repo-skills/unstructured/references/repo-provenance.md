# Repo Provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from the Unstructured Python package repository.

## Source Snapshot

- Commit: `5ead69ad146986a647ccbb4219ce94844710f4a9`
- Branch: `main`
- Exact tag: `0.23.1`
- Package distribution: `unstructured`
- Package version: `0.23.1`
- Working tree state: dirty because this generated `skills/` tree was added during skill creation.
- Remote URL: https://github.com/Unstructured-IO/unstructured

## Evidence Paths

The skill content was distilled from these repository-relative evidence groups:

- `README.md`
- `pyproject.toml`
- `Makefile`
- `unstructured/__version__.py`
- `unstructured/cli.py`
- `unstructured/doctor.py`
- `unstructured/partition/`
- `unstructured/file_utils/`
- `unstructured/documents/`
- `unstructured/staging/`
- `unstructured/common/`
- `unstructured/chunking/`
- `unstructured/cleaners/`
- `unstructured/nlp/`
- `unstructured/embed/`
- `unstructured/metrics/`
- `example-docs/`
- `test_unstructured/partition/`
- `test_unstructured/documents/`
- `test_unstructured/staging/`
- `test_unstructured/chunking/`
- `test_unstructured/cleaners/`
- `test_unstructured/nlp/`
- `test_unstructured/embed/`
- `test_unstructured/metrics/`
- `scripts/collect_env.py`
- `scripts/convert/`
- `scripts/user/`

## Inspection Baseline

Private package inspection verified:

- Distribution metadata for `unstructured` version `0.23.1`.
- Imports for core package, CLI/doctor, partitioning modules, element/staging modules, chunking modules, cleaners, core metrics, and embedding interfaces.
- CLI help for `python -m unstructured.cli` and `python -m unstructured.cli doctor`.
- Public signatures for `partition()`, `partition_text()`, `partition_html()`, `chunk_elements()`, `chunk_by_title()`, `elements_to_json()`, and `elements_from_json()`.

The inspection intentionally skipped broad `all-docs`, `ingest`, provider-credential, service, benchmark, hardware, torch/object-detection, and heavyweight model workflows. A tiny live `partition_text()` smoke attempt timed out in the private inspection environment, so this skill does not claim that partition execution was verified during generation.

## Refresh Guidance

Refresh this skill when any of these change:

- `pyproject.toml` dependency extras, Python range, or console entry points.
- Partition signatures, strategy behavior, file type mapping, or doctor diagnostics.
- Element JSON schema, metadata fields, coordinates, table metadata, or staging outputs.
- Chunking option validation, defaults, or output element types.
- Embedding provider modules, config classes, or credential requirements.
- Metrics calculators, table/object detection metrics, or output formats.
