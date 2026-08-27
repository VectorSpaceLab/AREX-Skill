---
schema: disco.repo-provenance.v1
---

# Repo Provenance

This repo skill was distilled from the Upsonic repository snapshot inspected in the current checkout.

## Snapshot

| Field | Value |
| --- | --- |
| Package | `upsonic` |
| Version | `0.77.3` |
| Git branch | `master` |
| Git commit | `101f0313b0ddb96cd4078354879b2ff57005db29` |
| Working tree | clean |
| Python requirement | `>=3.10` |

## Evidence paths used

- `README.md`
- `pyproject.toml`
- `src/upsonic/__init__.py`
- `src/upsonic/agent/agent.py`
- `src/upsonic/direct.py`
- `src/upsonic/chat/chat.py`
- `src/upsonic/team/team.py`
- `src/upsonic/tasks/tasks.py`
- `src/upsonic/knowledge_base/knowledge_base.py`
- `src/upsonic/tools/`
- `src/upsonic/skills/`
- `src/upsonic/storage/`
- `src/upsonic/cli/`
- `src/upsonic/prebuilt/`
- `tests/unit_tests/`
- `tests/smoke_tests/`
- `tests/doc_examples/`

## Staleness rule

Refresh this repo skill if the package version, public exports, CLI commands, or optional extras change in a newer checkout. The easiest signal is a mismatch between this file and the live `pyproject.toml` / `src/upsonic/__init__.py` snapshot.
