---
name: data-preparation
description: "Prepare and validate OpenFold FASTA, mmCIF, MSA, alignment DB,
  cache, duplicate-chain, and cluster-file inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenFold Data Preparation

Use this sub-skill when the task is about OpenFold input data rather than running prediction, training, installation, or model internals. It covers FASTA records, precomputed MSA/template layouts, `alignment_db.index`, mmCIF and chain caches, duplicate-chain metadata, cluster files, and safe dry-run validation.

## Route First

- Read `references/data-formats.md` for concrete FASTA, alignment directory, alignment DB, mmCIF cache, chain cache, duplicate-chain, and cluster-file layouts.
- Read `references/alignment-workflows.md` to plan precomputed alignment use, alignment DB conversion, and external binary/database requirements without launching expensive searches.
- Read `references/cache-and-db-workflows.md` to plan mmCIF/chain caches, duplicate-chain expansion, alignment DB shards, cluster files, and training data readiness checks.
- Read `references/api-reference.md` for parser, data-pipeline, multimer-pipeline, feature-pipeline, and cache-generation API expectations.
- Read `references/troubleshooting.md` when OpenFold reports malformed FASTA/MSA/mmCIF data, missing alignment files, stale index byte ranges, cache mismatches, duplicate-chain/cluster problems, missing external binaries, or build-extension import errors.

## Bundled Safe Helpers

- `scripts/validate_alignment_layout.py` checks local precomputed alignment directories and `alignment_db.index` files for expected OpenFold filenames, FASTA-to-directory key matching, shard references, byte ranges, duplicate-chain coverage, and multimer `uniprot_hits.sto` pairing inputs.
- `scripts/inspect_mmcif_cache.py` validates `mmcif_cache.json`, `chain_cache.json`, or `chain_data_cache.json` shape and reports missing keys, inconsistent chain/sequence counts, cluster mismatches, duplicate-chain coverage gaps, missing `.cif` files, and missing release-date/obsolete-entry planning inputs.
- `scripts/plan_alignment_db.py` dry-runs an alignment DB sharding plan from a flattened alignment directory and optional duplicate-chain file. It prints a plan only and does not create DB files, indexes, symlinks, clusters, downloads, or OpenFold features.

## Boundaries

- Route prediction command construction and inference execution to `../inference/` after data inputs validate.
- Route training command construction and training execution to `../training/` after caches, cluster files, and alignment inputs validate.
- Route database downloads, parameter downloads, binary installation, and environment repair to `../installation-assets/`.
- Route model configs, checkpoint conversion, attention kernels, protein object internals, and feature tensor interpretation to `../model-apis/`.

## Safety Rules

- Do not run downloads, HH-suite, HMMER, MMseqs, full cache generation, DB creation, inference, or training as a side effect of validation.
- Do not tell users to run source-checkout scripts by path. Use the bundled validators/planners here, or describe heavy OpenFold data utilities as explicit, user-approved reference operations.
- Keep local checkout paths, private environment paths, cache directories, credentials, and machine-specific install details out of public instructions, examples, and reports.
