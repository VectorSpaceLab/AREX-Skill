# Data Preparation Troubleshooting

Use this reference for OpenFold errors that mention FASTA parsing, alignment files, `alignment_db.index`, mmCIF parsing, cache JSON, duplicate chains, cluster files, missing external alignment binaries, or lightweight environments that cannot import full model extensions.

## Quick Triage

1. Identify the mode: monomer directory, multimer parent directory, AlphaFold-Gap multi-sequence directory, sequence-embedding/SoloSeq, training directory, or alignment DB index.
2. Run `validate_alignment_layout.py` on the alignment input.
3. Run `inspect_mmcif_cache.py` on any `mmcif_cache.json`, `chain_cache.json`, or `chain_data_cache.json` involved.
4. Confirm FASTA descriptions match alignment subdirectories or index keys.
5. Check duplicate-chain and cluster-file coverage for training data.
6. Route command-building problems to `../inference/` or `../training/` only after data layout validates.

## Missing Alignment Directory or Files

Symptoms:

- `FileNotFoundError` for an alignment directory.
- `Alignments for <chain> not found` from multimer processing.
- Empty MSA features or `At least one MSA must be provided`.
- Multimer chain not found under the parent alignment directory.

Likely causes:

- FASTA description does not match subdirectory name or index key.
- A monomer command points at the parent directory instead of the target directory.
- A multimer command points at one chain directory instead of the parent directory.
- Only template files are present; no `*.a3m` or supported `*.sto` MSA files are available.
- `seqemb_mode=True` was intended, but `*.pt` sequence embeddings are absent.

Safe check:

```bash
python scripts/validate_alignment_layout.py \
  --mode multimer \
  --alignment-dir multimer_alignments \
  --fasta multimer.fasta
```

Fix by renaming alignment subdirectories to match FASTA descriptions, correcting the command’s alignment path, or regenerating missing alignments.

## Malformed FASTA

Symptoms:

- `More than one input sequence found` in monomer `process_fasta`.
- Multimer chains are searched under unexpected names.
- AlphaFold-Gap multi-sequence runs strip descriptions to unexpected first tokens.

Likely causes:

- Monomer workflow received a multi-record FASTA.
- FASTA headers include spaces, and different OpenFold paths use full descriptions or first tokens differently.
- Sequence lines contain invalid characters, comments in the wrong place, or accidental blank records.

Fix by using one record for monomer, one record per chain for multimer, and stable whitespace-free IDs such as `target_A` or `chain_B`.

## Malformed MSA or Template Files

Symptoms:

- Parser errors from `parse_a3m`, `parse_stockholm`, `parse_hhr`, or HMMsearch template parsing.
- MSA sequence/deletion-matrix length mismatches.
- Template hits missing despite a template file being present.

Likely causes:

- File extension does not match content format.
- Stockholm file lacks a query row or terminator conventions expected by the parser.
- A3M file contains malformed FASTA headers or sequence lines.
- HMMsearch output is named incorrectly; directory mode expects `hmm_output.sto`, while index-backed template parsing recognizes `hmmsearch_output.sto`.

Fix by regenerating the affected alignment/template file with the matching external tool and preserving the OpenFold-expected filename.

## Missing Multimer `uniprot_hits.sto`

Symptoms:

- Heteromeric multimer processing raises `Missing 'uniprot_hits.sto'`.
- Index-backed multimer pairing fails while monomer parsing succeeds.

Likely causes:

- UniProt all-sequence search was skipped.
- The file exists under a different name.
- The top-level `alignment_db.index` entry for a chain lacks `uniprot_hits.sto`.

Fix by generating or restoring `uniprot_hits.sto` for heteromer chains, or intentionally use a workflow that does not require all-sequence MSA pairing.

## Stale or Broken `alignment_db.index`

Symptoms:

- Referenced shard file is missing.
- Seek/read errors from DB-backed alignment loading.
- Validator reports `offset + length` beyond shard size.
- Training sees fewer chains than expected.

Likely causes:

- DB shard files were moved without the index.
- The index was copied from a different DB build.
- Duplicate-chain expansion was skipped for index-backed data.
- A partial DB creation run left stale or truncated shard files.

Safe check:

```bash
python scripts/validate_alignment_layout.py \
  --mode index \
  --alignment-dir alignment_dbs \
  --alignment-index alignment_dbs/alignment_db.index \
  --json
```

Fix by rebuilding the alignment DB and index together, restoring missing shard files, or regenerating duplicate-chain aliases during DB creation.

## mmCIF Parse Failures

Symptoms:

- `mmcif_object` is `None` in a parsing result.
- Cache generation skips structures.
- Missing `release_date`, `resolution`, `chain_ids`, or sequence data in cache output.

Likely causes:

- File is not valid mmCIF content despite a `.cif` suffix.
- Filename stem does not match the expected structure ID.
- Required release-date or obsolete-entry metadata is unavailable for the target workflow.
- Structure contains nonstandard or empty chains that do not produce sequence records.

Fix by validating a small mmCIF subset first, replacing malformed structures, and ensuring release-date/obsolete metadata is included in the cache-generation plan.

## Cache Mismatch

Symptoms:

- Training samples refer to chain IDs absent from caches.
- Template filtering uses wrong release dates.
- `cluster_size` or `cluster_sizes` is missing or `-1` for many chains.
- `no_chains` does not match lengths of `chain_ids` and `seqs`.

Safe checks:

```bash
python scripts/inspect_mmcif_cache.py \
  --cache mmcif_cache.json \
  --kind mmcif \
  --mmcif-dir mmcifs
```

```bash
python scripts/inspect_mmcif_cache.py \
  --cache chain_data_cache.json \
  --kind chain \
  --cluster-file all-seqs_clusters-40.txt
```

Fix by regenerating caches from the same structure files, duplicate-chain file, and cluster file that training will consume.

## Duplicate-Chain and Cluster Problems

Symptoms:

- Directory-backed training has fewer chain directories than cache entries.
- Index-backed training has no duplicate keys for homomers.
- `cluster_size` values are missing, `-1`, or inconsistent.

Likely causes:

- Duplicate-chain expansion was skipped for directory-backed alignments.
- DB creation did not receive the duplicate-chain file.
- Cluster file was generated from a different FASTA or different chain ID case.

Fix by planning duplicate coverage with `plan_alignment_db.py`, validating duplicate coverage with `validate_alignment_layout.py --duplicate-chains-file`, regenerating FASTA from the final alignment layout, recreating the cluster file, and regenerating chain caches.

## Missing External Binaries or Databases

Symptoms:

- `jackhmmer`, `hhblits`, `hhsearch`, `hmmsearch`, `kalign`, or `mmseqs` not found.
- Alignment precomputation exits before writing expected files.
- Cluster-file generation fails.

Likely causes:

- Runtime environment lacks the external binary.
- Database path points to a missing or incomplete database root.
- User tried to run a full search from a lightweight inspection environment.

Route setup to `../installation-assets/`. Do not run full downloads or searches without explicit user approval and a runtime environment with enough disk/CPU/GPU resources.

## OpenFold Import Extension Failure

Symptoms:

- Basic metadata, config, or parser imports work, but model or CLI imports fail with `attn_core_inplace_cuda` missing.
- Data validators in this sub-skill work, but inference or training commands cannot start.

Likely cause:

- The OpenFold CUDA attention extension is not built or is not importable in the active environment.

Fix by routing environment repair to `../installation-assets/` and model-runtime troubleshooting to `../model-apis/`. Do not diagnose this as a malformed FASTA, MSA, mmCIF, cache, or alignment DB problem.

## Safe Recovery Order

1. Validate FASTA and alignment layout.
2. Validate index offsets if using alignment DBs.
3. Validate mmCIF and chain cache JSON shape.
4. Check duplicate-chain and cluster-file coverage.
5. Rebuild only the smallest stale artifact.
6. Re-run validators before starting inference or training.
