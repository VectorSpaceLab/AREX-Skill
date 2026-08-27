# Repo Provenance

## Source Snapshot

- vcs: git
- commit: `9d14a5e06d98355e5c0eccd0736b961fbe419f87`
- branch: `master`
- exact tag: none
- remote_url: https://github.com/langchain-ai/langchain
- dirty checkout: yes, generated `skills/` content was present at generation time

## Package Versions Observed from Metadata

- `langchain-core`: 1.4.8 from `libs/core/pyproject.toml`
- `langchain`: 1.3.10 from `libs/langchain_v1/pyproject.toml`
- `langchain-classic`: 1.0.8 from `libs/langchain/pyproject.toml`
- `langchain-text-splitters`: 1.1.2 from `libs/text-splitters/pyproject.toml`
- `langchain-tests`: 1.1.9 from `libs/standard-tests/pyproject.toml`

## Inspection Environment

Live installed-package inspection was not completed because `uv` was unavailable in the host environment and the repository instructions require `uv` for environment and dependency operations. This skill is based on repository source, metadata, docs, tests, and scripts, with verification artifacts recording the skipped live-inspection gate.

## Evidence Paths

- `AGENTS.md`
- `README.md`
- `libs/README.md`
- `libs/core/pyproject.toml`, `libs/core/langchain_core/`, `libs/core/tests/`
- `libs/langchain_v1/pyproject.toml`, `libs/langchain_v1/langchain/`, `libs/langchain_v1/tests/`
- `libs/langchain/pyproject.toml`, `libs/langchain/langchain_classic/`, `libs/langchain/tests/`
- `libs/text-splitters/pyproject.toml`, `libs/text-splitters/langchain_text_splitters/`, `libs/text-splitters/tests/`
- `libs/partners/*/pyproject.toml`, `libs/partners/*/langchain_*`, `libs/partners/*/tests/`, `libs/partners/*/scripts/`
- `libs/standard-tests/pyproject.toml`, `libs/standard-tests/langchain_tests/`
- `libs/model-profiles/pyproject.toml`, `libs/model-profiles/langchain_model_profiles/`

## Dirty Paths Summary

The checkout was dirty because this skill generation created new `skills/` content. Other changed paths, if any, should be reviewed with `git status --short` before using this provenance as a refresh baseline.
