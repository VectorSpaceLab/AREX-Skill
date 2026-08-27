---
name: webdataset
description: "Guide WebDataset shard loading, shard writing, and
  opener/cache/security workflows for shard-based data pipelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# WebDataset

Use this repo skill when the task names WebDataset, tar shards, shard lists, tar-member grouping, `WebDataset`, `WebLoader`, `DataPipeline`, `TarWriter`, `ShardWriter`, `gopen`, cache directories, secure mode, or read/write errors around shard-based datasets.

## Start here

- Read [Repository provenance](references/repo-provenance.md) when you need to check whether this skill matches the current checkout or when a repo refresh might be needed.
- Read [API reference overview](references/api-reference.md) for the verified package surface and the three main workflow families.
- Read [Configuration](references/configuration.md) for install patterns, optional dependencies, and the environment variables that change behavior.
- Read [Data formats](references/data-formats.md) when you need shard naming, sample layout, or extension-driven encoding/decoding rules.
- Read [Troubleshooting](references/troubleshooting.md) first for install, import, reader, writer, and opener failures.
- Run [scripts/check_env.py](scripts/check_env.py) when you need a tiny offline import-and-roundtrip check.

## Route map

### Reading and loading

Use [sub-skills/reading-pipelines/SKILL.md](sub-skills/reading-pipelines/SKILL.md) for shard consumption, filters, decoding, tuple projection, batching, `DataLoader`/`WebLoader`, shard splitting, mixing, and column-store style read flows.

Typical triggers:

- "How do I read WebDataset shards?"
- "How do I use `WebLoader` or `DataPipeline`?"
- "Why do I get empty shards or missing keys?"
- "How do I decode images or tuples from tar samples?"
- "How do I split by worker or node?"

### Shard writing

Use [sub-skills/shard-writing/SKILL.md](sub-skills/shard-writing/SKILL.md) for `TarWriter`, `ShardWriter`, writer encoders, rollover patterns, and local read-back validation.

Typical triggers:

- "How do I create WebDataset tar files?"
- "How do I use `ShardWriter` rollover?"
- "How do I encode images, JSON, NumPy arrays, or text?"
- "How do I validate a shard after writing it?"
- "How do I turn a dataset generation recipe into a tiny local writer?"

### Openers, cache, and security

Use [sub-skills/io-caching-security/SKILL.md](sub-skills/io-caching-security/SKILL.md) for `gopen`, stream caching, `pipe:` trust boundaries, custom schemes, secure mode, and handler selection.

Typical triggers:

- "Why is `pipe:` failing?"
- "How do I configure `WDS_SECURE`?"
- "How does `FileCache` name or clean files?"
- "How do I add a custom opener scheme?"
- "Why is a local file or pickle blocked?"

## What this skill is not

- It is not a generic model-training or model-serving skill.
- It is not a repository-maintenance skill for editing the source checkout.
- It does not teach credentialed cloud setup, GPU training, OCR engines, or notebook execution as primary runtime behavior.

## Minimal install check

For ordinary use, install the package and confirm it imports:

```bash
pip install webdataset
python scripts/check_env.py
```

If the task needs a real PyTorch loader, run:

```bash
python scripts/check_env.py --require-torch
```

If you are developing against a checkout rather than a release wheel, install editable mode and keep the environment small unless the task needs an optional dependency listed in `references/configuration.md`.

## How to think about the package

- The package is centered on tar shards whose members are grouped by basename.
- Reading tasks usually involve expanding shard lists, splitting by worker or node, decoding payloads, then filtering or batching.
- Writing tasks usually involve a flat sample dict, stable `__key__` values, extension-driven encoders, and read-back validation.
- Openers and caches are a trust boundary: treat `pipe:` and URL rewriting as intentional choices, not defaults.

## Quick routing hints

- If the task starts with existing shards, route to reading.
- If the task starts with creating shards, route to writing.
- If the task starts with URL, cache, or security issues, route to opener/security.
- If the request mixes all three, begin with the root references above, then move into the owning sub-skill.

## Bundled references and helpers

- [references/api-reference.md](references/api-reference.md) — verified package surface and top-level workflow families.
- [references/configuration.md](references/configuration.md) — install and environment variables.
- [references/data-formats.md](references/data-formats.md) — shard and sample conventions.
- [references/troubleshooting.md](references/troubleshooting.md) — cross-cutting failures and the first recovery step.
- [scripts/check_env.py](scripts/check_env.py) — tiny offline import and round-trip check.

Keep runtime guidance inside this skill tree. Do not point future agents back to the original repository checkout for ordinary package use.
