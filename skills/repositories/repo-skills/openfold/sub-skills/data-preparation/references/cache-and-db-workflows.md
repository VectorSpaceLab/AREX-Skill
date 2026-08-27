# Cache and Database Workflows

OpenFold training data preparation combines structure files, precomputed alignments, duplicate-chain metadata, sequence clusters, and optional alignment DB shards. This reference explains the workflows without depending on source-checkout scripts.

## Training Data Layout Overview

A practical OpenProteinSet-style layout often looks like:

```text
data_root/
  pdb_data/
    duplicate_pdb_chains.txt
    mmcifs/
      3lrm.cif
      6kwc.cif
    data_caches/
      mmcif_cache.json
      chain_data_cache.json
  alignment_data/
    alignments/
      3lrm_A/
      3lrm_B/
    alignment_dbs/
      alignment_db_0.db
      alignment_db_1.db
      alignment_db.index
    all-seqs.fasta
    all-seqs_clusters-40.txt
```

Directory-backed training uses `alignment_data/alignments/<chain_id>/`. Index-backed training uses `alignment_data/alignment_dbs/` plus `alignment_db.index`.

## mmCIF Cache Workflow

`mmcif_cache.json` summarizes each mmCIF entry for template filtering and data loading. Required inputs are local mmCIF files; optional cluster information can be included when a cluster file exists.

Plan for a custom dataset:

1. Collect mmCIF files under one directory with stable filename stems such as `1abc.cif`.
2. Confirm each mmCIF has parseable chain IDs, sequences, release date, and resolution.
3. Prepare release-date and obsolete-entry metadata if downstream template filtering depends on PDB revision dates.
4. Decide whether cluster sizes should be attached to the mmCIF cache using a cluster file.
5. Generate a cache in the shape shown in `references/data-formats.md`.
6. Validate the produced cache with `scripts/inspect_mmcif_cache.py`.

Safe validation:

```bash
python scripts/inspect_mmcif_cache.py \
  --cache mmcif_cache.json \
  --kind mmcif \
  --mmcif-dir mmcifs \
  --require-release-dates
```

This checks JSON shape and optionally reports cache entries missing corresponding local `.cif` files, local `.cif` files missing from the cache, and structures missing usable release dates.

## Chain Cache Workflow

`chain_data_cache.json` or `chain_cache.json` summarizes individual chains for training sample filtering and cluster-size weighting.

Plan:

1. Ensure mmCIF or PDB files use stable structure IDs.
2. Prepare a cluster file if inverse-cluster sampling should be represented.
3. Generate one entry per full chain ID, typically `<pdb_id>_<chain_id>`.
4. Include `release_date`, `seq`, `resolution`, and optionally `cluster_size`.
5. Validate chain cache shape and chain IDs.

Safe validation:

```bash
python scripts/inspect_mmcif_cache.py \
  --cache chain_data_cache.json \
  --kind chain \
  --cluster-file all-seqs_clusters-40.txt
```

Missing `cluster_size` is acceptable only when the training plan intentionally does not use cluster-aware sampling.

## Duplicate-Chain Expansion

OpenProteinSet stores representative alignments for identical chains and a duplicate-chain file listing equivalent chains:

```text
3lrm_A 3lrm_B 3lrm_C 3lrm_D
6kwc_A
```

For directory-backed alignments, duplicate expansion creates missing chain directories or symlinks pointing to the representative chain. For alignment DBs, duplicate expansion adds extra index keys that reuse the representative shard offsets.

Safe planning checks:

- Every non-empty duplicate group has at least one representative alignment directory or index key.
- Adding duplicate names will not overwrite an existing non-representative chain entry unexpectedly.
- Duplicate chain IDs use the same case convention as cache and cluster files.
- Index-backed duplicate entries are intentional aliases; changing one representative’s shard bytes affects every duplicate key.

Use `plan_alignment_db.py --duplicate-chains-file` to report representative coverage without creating symlinks or index entries. Use `validate_alignment_layout.py --duplicate-chains-file` to compare an existing directory or index against duplicate groups.

## Alignment DB Sharding Workflow

An alignment DB packs many alignment files into fewer binary shard files and records byte ranges in `alignment_db.index`.

Recommended planning steps:

1. Start with a flattened alignment directory containing one subdirectory per chain.
2. Validate that representative chain directories contain at least one MSA file and expected template files.
3. Choose shard count. Ten shards is a common OpenProteinSet recommendation, but use fewer for tiny datasets and avoid more shards than available CPUs for creation.
4. Include duplicate-chain metadata during DB creation if the dataset uses representative alignments.
5. Validate the resulting `alignment_db.index` before training.

Safe planner:

```bash
python scripts/plan_alignment_db.py \
  --alignment-dir alignment_data/alignments \
  --output-db-name alignment_db \
  --n-shards 10 \
  --duplicate-chains-file pdb_data/duplicate_pdb_chains.txt \
  --json
```

Safe index validator:

```bash
python scripts/validate_alignment_layout.py \
  --mode index \
  --alignment-dir alignment_data/alignment_dbs \
  --alignment-index alignment_data/alignment_dbs/alignment_db.index
```

## Alignment DB Index Shape

The index must be a JSON object:

```json
{
  "6kwc_A": {
    "db": "alignment_db_1.db",
    "files": [
      ["bfd_uniclust_hits.a3m", 415618723280, 380289],
      ["mgnify_hits.a3m", 415618556077, 167203]
    ]
  }
}
```

Validation rules:

- Top-level keys should be chain IDs.
- `db` must be a relative shard filename, not an absolute path.
- `files` must be a list of three-item records.
- Offsets and lengths must be nonnegative integers.
- The referenced shard file must exist under the provided alignment DB directory.
- `offset + length` must be within the shard file size.
- Each chain should include at least one MSA file; template files alone do not produce MSA features.
- Index-backed HMMsearch template records should be named `hmmsearch_output.sto`.

## Cluster File Workflow

Training setup commonly creates `all-seqs.fasta` and clusters it with MMseqs at 40% sequence identity:

```text
all-seqs.fasta
all-seqs_clusters-40.txt
```

The cluster file has one cluster per line. Each chain in the chain cache should appear in exactly one line when cluster-aware sampling is intended. If a chain is absent, cache generation may record `cluster_size: -1` or omit `cluster_size`, which should be reviewed before long training runs.

## Custom Dataset Checklist

Before handing data to training:

- FASTA headers, alignment directory names, cache keys, duplicate-chain entries, and cluster entries use the same full-chain IDs.
- `mmcif_cache.json` and `chain_data_cache.json` pass `inspect_mmcif_cache.py`.
- Directory-backed alignments pass `validate_alignment_layout.py --mode training-dir`.
- Index-backed alignments pass `validate_alignment_layout.py --mode index`.
- Duplicate-chain groups have at least one representative in the chosen alignment layout.
- Cluster-aware training has a chain cache whose `cluster_size` values are positive for expected train chains.
- Template databases, obsolete-entry metadata, and release-date cutoffs are accounted for by the inference/training workflow.
- Heavy operations such as downloads, alignment search, MMseqs clustering, and DB creation have explicit user approval and enough disk/CPU resources.
