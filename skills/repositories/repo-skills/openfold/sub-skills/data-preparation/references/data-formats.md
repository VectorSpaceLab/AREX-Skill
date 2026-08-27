# OpenFold Data Formats

This reference describes data files OpenFold expects before inference or training. It is self-contained and avoids source-checkout paths.

## FASTA Inputs

OpenFold parser behavior is simple: `parse_fasta(fasta_string)` returns sequences first and descriptions second, ignores blank lines and `#` comment lines, and preserves the whole text after `>` as the description.

- Monomer `DataPipeline.process_fasta` expects exactly one FASTA record.
- AlphaFold-Gap style `DataPipeline.process_multiseq_fasta` accepts multiple records, strips each description to its first whitespace-delimited token, and joins sequences internally.
- `DataPipelineMultimer.process_fasta` accepts one record per chain and uses the full parsed description string as the chain key for alignment subdirectories or top-level index lookup; use whitespace-free descriptions to avoid accidental mismatches.
- Stable IDs matter because FASTA description tokens are used to find `alignment_dir/<description>/` or `alignment_db.index[description]`.
- Sequence lines may wrap, but empty records, sequence text before the first header, and unexpected characters should be fixed before feature generation.

Example monomer FASTA:

```text
>target_A
MSEQNNTEMTFQIQRIYTKDISFEAPNAPHVFQKDW
```

Example multimer FASTA:

```text
>chain_A
MSEQNNTEMTFQIQRIYTKDISFEAPNAPHVFQKDW
>chain_B
GVLFDYEAQSGKHGEEAKRAV
```

## Precomputed Alignment Directory Layouts

OpenFold can consume precomputed alignment/template files from directories instead of rerunning searches.

### Monomer or Single-Chain Directory

A monomer alignment directory is passed directly as `alignment_dir`:

```text
alignments_for_target/
  bfd_uniclust_hits.a3m
  mgnify_hits.sto
  uniref90_hits.sto
  pdb70_hits.hhr
```

OpenFold parser treatment:

- `*.a3m`: ordinary MSA parsed by `parse_a3m`.
- `*.sto`: ordinary MSA parsed by `parse_stockholm`, except files named `uniprot_hits.sto` and `hmm_output.sto` are excluded from ordinary MSA parsing.
- `*.hhr`: HHsearch template hits parsed by `parse_hhr`.
- `hmm_output.sto`: HMMsearch template hits in directory-backed workflows.
- `*.pt`: sequence-embedding file used only when `seqemb_mode=True`.

Common filenames vary by workflow. Inference examples often use `mgnify_hits.sto`, `uniref90_hits.sto`, and `pdb70_hits.hhr`; training alignment DB examples often use `mgnify_hits.a3m`, `uniref90_hits.a3m`, `bfd_uniclust_hits.a3m`, and `pdb70_hits.hhr`.

### Flattened Training Directory

Directory-backed training expects one subdirectory per chain, normally named `<pdb_id>_<chain_id>`:

```text
alignment_data/
  alignments/
    3lrm_A/
      bfd_uniclust_hits.a3m
      mgnify_hits.a3m
      pdb70_hits.hhr
      uniref90_hits.a3m
    3lrm_B/
      bfd_uniclust_hits.a3m
      mgnify_hits.a3m
      pdb70_hits.hhr
      uniref90_hits.a3m
```

The chain IDs in this directory should match cache keys, duplicate-chain file entries, cluster-file entries, FASTA headers, and `alignment_db.index` keys.

### Multimer Directory

For multimer data without an index, the parent alignment directory contains one subdirectory for each FASTA description:

```text
multimer_alignments/
  chain_A/
    bfd_uniclust_hits.a3m
    mgnify_hits.sto
    uniref90_hits.sto
    uniprot_hits.sto
    hmm_output.sto
  chain_B/
    bfd_uniclust_hits.a3m
    mgnify_hits.sto
    uniref90_hits.sto
    uniprot_hits.sto
    hmm_output.sto
```

`DataPipelineMultimer` uses `uniprot_hits.sto` for all-sequence MSA pairing when the FASTA contains two or more unique sequences. Homomers and monomers may skip pairing features, but missing `uniprot_hits.sto` is a common heteromer failure.

## Alignment DB Layout

OpenFold can pack many small alignment files into shard files and use a JSON index to seek into each shard. This is useful for large training datasets where one directory per chain is slow.

Expected layout:

```text
alignment_dbs/
  alignment_db_0.db
  alignment_db_1.db
  alignment_db_2.db
  alignment_db.index
```

`alignment_db.index` is a JSON object keyed by chain ID. Each entry has:

```json
{
  "3lrm_A": {
    "db": "alignment_db_0.db",
    "files": [
      ["bfd_uniclust_hits.a3m", 0, 1200],
      ["mgnify_hits.a3m", 1200, 800],
      ["pdb70_hits.hhr", 2000, 300],
      ["uniref90_hits.a3m", 2300, 1500]
    ]
  }
}
```

Validation rules:

- `db` is a relative shard filename stored beside or under the supplied alignment DB directory.
- Every file record has `[filename, byte_offset, byte_length]`.
- Offsets and lengths are nonnegative integers.
- `byte_offset + byte_length` must not exceed the shard file size.
- Each entry should contain at least one ordinary MSA (`*.a3m` or non-excluded `*.sto`) unless sequence-embedding mode is intentional.
- For index-backed HMMsearch template hits, OpenFold recognizes `hmmsearch_output.sto`; for directory-backed HMMsearch template hits, it recognizes `hmm_output.sto`.
- For multimer heteromers, index entries should include `uniprot_hits.sto` for all-sequence pairing.

## mmCIF Files

OpenFold parses structure files from mmCIF strings with `mmcif_parsing.parse(file_id=..., mmcif_string=...)`. Training data commonly stores structures as lowercase PDB IDs:

```text
pdb_data/
  mmcifs/
    3lrm.cif
    6kwc.cif
```

The `file_id` should match the filename stem and cache keys that refer to the structure. mmCIF parsing should expose release date, resolution, chain IDs, and sequence records for cache generation.

## mmCIF Cache Schema

`mmcif_cache.json` is keyed by structure ID and stores metadata condensed by mmCIF entry:

```json
{
  "3lrm": {
    "release_date": "2010-06-30",
    "chain_ids": ["A", "B", "C", "D"],
    "seqs": ["MFAF...", "MFAF...", "MFAF...", "MFAF..."],
    "no_chains": 4,
    "resolution": 2.7
  }
}
```

Required keys are `release_date`, `chain_ids`, `seqs`, `no_chains`, and `resolution`. `chain_ids` and `seqs` must have the same length, and `no_chains` should equal that length. Generated caches may also include `cluster_sizes` aligned with `chain_ids`; absent or `-1` cluster sizes should be reviewed for training.

## Chain Cache Schema

`chain_cache.json` or `chain_data_cache.json` is keyed by full chain ID:

```json
{
  "3lrm_A": {
    "release_date": "2010-06-30",
    "seq": "MFAFYFLTACISLKG...",
    "resolution": 2.7,
    "cluster_size": 6
  }
}
```

Required keys are `release_date`, `seq`, and `resolution`. `cluster_size` is expected when a cluster file was supplied during cache generation; missing or nonpositive values indicate chains that may not be represented in the cluster file.

## Duplicate-Chain File

Duplicate chains are stored as whitespace-separated groups where every chain in a line has identical sequence:

```text
6kwc_A
3lrm_A 3lrm_B 3lrm_C 3lrm_D
```

Directory-backed training can expand representative alignments into missing duplicate directories. Index-backed training can add duplicate keys that point to the representative shard offsets. Keep duplicate-chain IDs in the same case convention as alignment directories, index keys, caches, and clusters.

## Cluster File

A cluster file contains one sequence cluster per line, with full chain IDs separated by whitespace:

```text
3lrm_A 3lrm_B 3lrm_C 3lrm_D
6kwc_A
```

Training sample weighting uses inverse cluster size. Every chain in `chain_data_cache.json` should appear in exactly one cluster line when cluster-aware sampling is intended.
