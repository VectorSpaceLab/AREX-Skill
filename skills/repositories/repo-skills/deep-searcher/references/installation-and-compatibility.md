# Installation and Compatibility

## Purpose

Use this reference when you need a quick install recipe, package identity check, or an explanation of the compatibility pins that mattered during skill generation.

## Package identity

- Distribution: `deepsearcher`
- Import module: `deepsearcher`
- Console script: `deepsearcher = deepsearcher.cli:main`
- Python requirement from package metadata: `>=3.10`

## Baseline install

For a standard package install:

```bash
pip install deepsearcher
```

For a development checkout, the repository docs recommend `uv sync`, but the generated skill should stay usable even when the original repository checkout is gone. Prefer the installed package plus the bundled helpers in this skill tree.

## Compatibility notes from the inspected checkout

The inspected checkout's default configuration and CLI/service paths relied on a compatible local Milvus stack and an older FireCrawl Python client:

```bash
pip install "firecrawl-py==2.16.5"
pip install "pymilvus==2.5.8" "milvus-lite==2.5.1" "setuptools<81"
```

Why these pins mattered:

- `firecrawl-py` 4.x exported `V1ScrapeOptions` but not the `ScrapeOptions` name imported by this checkout's FireCrawl crawler.
- `pymilvus` 3.x plus `milvus-lite` 3.x produced local Milvus smoke failures for this checkout.
- `milvus-lite` 2.5.1 imports `pkg_resources`, so `setuptools<81` keeps that API available.

Treat these as compatibility notes for the inspected tree, not as a universal requirement for every DeepSearcher deployment.

## Minimal environment sanity check

Run the bundled helper after installation:

```bash
python scripts/check_deepsearcher_environment.py
```

The helper reports installed versions and importability without contacting provider APIs or loading data. Add `--check-cli-help` if you want a temp-directory CLI probe.

## When to read the sub-skills

- Provider names, credentials, and optional extras: `sub-skills/provider-configuration/`
- Local/web data loading and chunking: `sub-skills/data-ingestion/`
- Query and retrieval workflows: `sub-skills/rag-query/`
- CLI/service behavior: `sub-skills/cli-and-service/`
- Evaluation workflow: `sub-skills/evaluation/`
