# Alignment Workflows

OpenFold can either run alignment searches or consume precomputed alignments. This sub-skill treats full searches as reference-only because they require large sequence/template databases, external binaries, substantial CPU, and sometimes network-prepared assets.

## Choose the Workflow

- Use precomputed alignments when a user already has `bfd_uniclust_hits`, `mgnify_hits`, `uniref90_hits`, `pdb70_hits`, `uniprot_hits`, or `hmm_output` files.
- Use directory validation before inference or training when debugging missing feature keys, missing templates, `FileNotFoundError`, or `ValueError` from OpenFold data pipelines.
- Use alignment DB planning when a dataset has many chain directories and training is I/O-bound.
- Route full database downloads and binary installation to `../installation-assets/`.
- Route prediction command construction to `../inference/` after alignments validate.
- Route training command construction to `../training/` after alignments, caches, clusters, and duplicate metadata validate.

## Precomputed Monomer Alignments

A monomer prediction can consume a single alignment directory:

```text
alignments_for_target/
  bfd_uniclust_hits.a3m
  mgnify_hits.sto
  uniref90_hits.sto
  pdb70_hits.hhr
```

Minimum practical checks:

1. The FASTA has exactly one record for `DataPipeline.process_fasta`.
2. The alignment directory exists and contains at least one parseable MSA file (`*.a3m` or a supported `*.sto`) unless `seqemb_mode=True` is intentionally used.
3. Template files match the template search mode: `pdb70_hits.hhr` for HHsearch/PDB70-style monomer templates, or `hmm_output.sto` for HMMsearch/PDB SeqRes style directory-backed templates.
4. File extensions match content. A Stockholm file renamed as `.a3m` will fail in `parse_a3m`, and an A3M file renamed as `.sto` will fail in `parse_stockholm`.

Safe helper:

```bash
python scripts/validate_alignment_layout.py \
  --mode monomer \
  --alignment-dir alignments_for_target \
  --fasta target.fasta
```

## Precomputed Multimer Alignments

For a multimer FASTA, the parent alignment directory must contain one subdirectory per FASTA description. Use whitespace-free descriptions to keep `DataPipelineMultimer` lookups unambiguous.

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

`uniprot_hits.sto` is used for all-sequence MSA pairing in heteromeric multimer runs. Missing `uniprot_hits.sto` may be acceptable for homomers or intentionally unpaired workflows, but it is a high-priority warning for heteromers.

Safe helper:

```bash
python scripts/validate_alignment_layout.py \
  --mode multimer \
  --alignment-dir multimer_alignments \
  --fasta multimer.fasta
```

## AlphaFold-Gap Multi-Sequence FASTA

`DataPipeline.process_multiseq_fasta` is distinct from `DataPipelineMultimer`. It strips each FASTA description to the first token, expects `super_alignment_dir/<token>/`, concatenates sequences internally with residue-index gaps, and does not use `uniprot_hits.sto` pairing features. Validate this input like a multimer parent directory, but document that it is a multi-sequence monomer-pipeline workflow rather than the multimer model pipeline.

## SoloSeq and Sequence-Embedding Alignments

SoloSeq workflows can avoid ordinary MSA features by using sequence embeddings. In API terms, `seqemb_mode=True` makes `DataPipeline.process_fasta` create dummy MSA features and read `*.pt` embedding files from the alignment directory.

Check that:

- The workflow is actually using a sequence-embedding config or command mode.
- The alignment directory contains the expected `*.pt` embedding file.
- Missing ordinary MSA files are intentional rather than a failed search.

Use `--allow-empty-msa --require-seqemb` with the validator when checking a sequence-embedding directory.

## Running Alignment Searches: Reference-Only Plan

OpenFold utilities can precompute alignments with HH-suite/HMMER tools or MMseqs-style searches, but generated skills should not launch them automatically. A future agent should only plan these commands after confirming resources and assets.

Typical binary/database requirements:

- `jackhmmer` with UniRef90, MGnify, and optionally UniProt databases.
- `hhblits` with BFD plus UniClust30 or UniRef30-style databases.
- `hhsearch` with PDB70 for monomer templates.
- `hmmsearch` with PDB SeqRes for multimer templates.
- `kalign` for template featurization workflows.
- `mmseqs` for clustering FASTA into cluster files or MMseqs alignment search workflows.

Reference-only planning checklist:

1. Decide monomer, multimer, AlphaFold-Gap multi-sequence, or SoloSeq/sequence-embedding mode.
2. Confirm FASTA headers that become alignment lookup keys.
3. Confirm database roots and external binaries exist in the user’s runtime environment.
4. Choose output layout: one target directory for inference, flattened chain directories for training, or sharded alignment DBs for large training sets.
5. Validate produced output before constructing inference or training commands.

## Alignment DB Conversion Workflow

For large training data, convert a flattened directory into shard files and one JSON index. Do not create DB files from this sub-skill; use `scripts/plan_alignment_db.py` to check readiness and estimate shards.

```bash
python scripts/plan_alignment_db.py \
  --alignment-dir alignment_data/alignments \
  --output-db-name alignment_db \
  --n-shards 10 \
  --duplicate-chains-file pdb_data/duplicate_pdb_chains.txt
```

The plan reports:

- Number of chain directories found.
- Alignment filenames observed per chain.
- Missing or empty common alignment files.
- Duplicate-chain groups whose representative is absent.
- Proposed shard filenames such as `alignment_db_0.db` through `alignment_db_9.db`.
- Whether any shard would be empty.

## Alignment-to-FASTA and Cluster Preparation

Training setup commonly derives a FASTA from either flattened alignments or `alignment_db.index`, then clusters sequences at 40% identity with MMseqs:

```text
alignment_data/all-seqs.fasta
alignment_data/all-seqs_clusters-40.txt
```

OpenFold’s alignment-to-FASTA utility extracts the query sequence from one of `mgnify_hits.a3m`, `uniref90_hits.a3m`, or `bfd_uniclust_hits.a3m`. If those files are absent or the query sequence is not the second line of the selected A3M content, FASTA conversion can fail or emit incorrect sequences. Validate alignment layout before clustering.

## When to Skip or Escalate

Ask for explicit confirmation before any operation that would:

- Download RODA/OpenProteinSet/AlphaFold databases or weights.
- Run HH-suite, HMMER, or MMseqs over nontrivial datasets.
- Modify large alignment directories or create duplicate-chain symlinks.
- Generate or rewrite production `alignment_db` shard files.
- Run OpenFold inference/training as a side effect of validation.
