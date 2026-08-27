# Data Formats

## FASTA Inputs

AlphaFold prediction inputs are FASTA files containing one or more protein sequences:

- One FASTA record is a monomer target for monomer model presets.
- Multiple FASTA records in one file are a multimer target for the multimer preset.
- Multiple separate FASTA files are folded sequentially by the prediction CLI; that orchestration belongs to `prediction-cli`.

Use strict protein validation before prediction:

- Allowed residue letters for notebook-style input validation are the 20 standard amino acids: `ACDEFGHIKLMNPQRSTVWY`.
- `B`, `J`, `O`, `U`, `X`, `Z`, gaps, digits, punctuation, and nucleotide letters not in the standard set should be rejected for raw input sequences.
- Whitespace inside sequence text may be removed and letters uppercased for validation.
- Empty FASTA records, too-short sequences, too-long sequences, and duplicate descriptions should be surfaced before prediction.

The low-level FASTA parser is intentionally permissive. It returns descriptions and concatenated sequence lines, but it does not enforce residue validity, length limits, duplicate labels, or target mode.

## Multimer Chain Semantics

For multimer FASTA files, each FASTA record is one chain copy. AlphaFold maps records to PDB-format chain IDs in this order:

```text
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789
```

The PDB-format limit is 62 chains. More than 62 records will fail in the multimer pipeline and also cannot be represented in AlphaFold PDB output.

Repeated sequences matter:

- A single unique sequence repeated multiple times is a homomer.
- Multiple unique sequences with some repeats represent a heteromer with copy numbers, such as A2B3.
- The multimer pipeline processes each unique sequence once and copies features for identical chains.
- Heteromers use UniProt all-sequence MSA features for pairing; homomers/monomers skip that pairing path.
- Reusing an MSA from a different chain count, sequence order, or target mode is unsafe even if the raw sequence strings look familiar.

## A3M Alignments

A3M is the alignment format commonly produced by HHblits and consumed by HHsearch/template workflows.

- Records are FASTA-like: `>` descriptions followed by sequence lines.
- Uppercase letters and gaps are aligned columns.
- Lowercase letters are insertions relative to the query and are removed from the aligned sequences returned by `parse_a3m`.
- The deletion matrix stores how many lowercase insertion residues occurred before each aligned residue.
- The first row should be the query sequence for AlphaFold feature construction assumptions.

Tiny A3M example:

```text
>query
ACEFG
>hit1
ACdEFG
```

The aligned hit sequence remains `ACEFG`; the lowercase `d` contributes to the deletion count before the next aligned residue.

## Stockholm Alignments

Stockholm (`.sto`) is commonly produced by JackHMMER/HMMER searches.

- Non-empty, non-comment, non-terminator lines contain a sequence name and an aligned sequence fragment.
- Sequence fragments with the same name are concatenated across blocks.
- The first sequence is treated as the query.
- Columns where the query has a gap are removed from all parsed MSA sequences.
- Deletion counts are computed for residues skipped relative to query positions.
- `#=GS <name> DE <description>` rows can become A3M descriptions during Stockholm-to-A3M conversion.

Tiny Stockholm-to-A3M reasoning case:

```text
# STOCKHOLM 1.0
query AC-DE
hit1  ACGDE
//
```

With first-row gap removal enabled, the query gap column is removed. The `G` in `hit1` at that removed query-gap column becomes a lowercase insertion in A3M, so downstream A3M parsing treats it as deletion-matrix information rather than an aligned query column.

## Template Inputs

Template featurization expects template-search hits plus local mmCIF structures:

- Hit names must include a parseable four-character PDB ID and chain identifier for HHsearch-style hits.
- Template mmCIF files are expected to be named by PDB ID with `.cif` suffix.
- `max_template_date` must be an ISO date string (`YYYY-MM-DD`) and excludes templates released after that date.
- Kalign is required to realign template sequences when the search hit sequence differs from the mmCIF chain sequence.
- Obsolete PDB mappings can redirect old IDs to replacement IDs.

Use template guidance to reason about validity, but do not run template search or featurization unless the user has explicitly requested an expensive local data-pipeline operation.

## Precomputed MSA Reuse

Precomputed MSA reuse is a path-based optimization, not a correctness check. AlphaFold reads existing MSA files from the output/MSA directory when configured to do so; it does not prove that the sequence, databases, search settings, or target mode still match. Treat reuse as valid only when all of these are intentionally unchanged:

- FASTA sequence content and chain order.
- Monomer versus multimer mode.
- Database preset and database snapshots.
- MSA tool versions and CPU/search parameters when reproducibility matters.
- Output directory and expected intermediate filenames.
