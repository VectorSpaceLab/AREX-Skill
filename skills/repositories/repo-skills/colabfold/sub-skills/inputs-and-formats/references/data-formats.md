# ColabFold data formats

ColabFold accepts single input files or directories. The input parser returns query records shaped like `(job_name, query_sequence, a3m_lines, template_path_or_none)` plus an `is_complex` flag. Input preparation should make the parser result predictable before any MSA search or prediction work starts.

## FASTA files

Supported suffixes are `.fasta`, `.faa`, and `.fa`.

```text
>job_name
MSEQUENCEAA
```

Rules:

- A FASTA header becomes the job name for a single FASTA file.
- Blank lines and lines beginning with `#` are ignored by `parse_fasta`.
- Sequences are uppercased for single FASTA files.
- In a directory, a FASTA file with multiple records uses only the first record and logs a warning.
- A colon inside the sequence string marks a complex unless it is part of an escaped AlphaFold3 SMILES entry as described below.

## Multimer and homooligomer syntax

Use colon-separated protein chains in one FASTA sequence:

```text
>heteromer_ab
MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQ:GSHMASMTGGQQMGRDLYDDDDK
```

Behavior:

- `get_queries` converts colon-separated protein FASTA into a list of chain sequences.
- Any query whose `query_sequence` is a list makes `is_complex=True`.
- Repeated identical chains are valid and are later treated as homooligomer/cardinality information by MSA and prediction code.
- Use unambiguous headers because output job names are sanitized by replacing characters outside letters, digits, `_`, `.`, and `-` with `_` in prediction workflows.

## CSV and TSV files

CSV/TSV inputs require `id` and `sequence` columns. Optional columns are `a3mpath` and `templatepath`.

```csv
id,sequence
monomer_1,YYDPETGTWY
complex_ab,MRILPISTIKGKLNEFVDAVSSTQDQITITKNGAPAAVLVGADEWESLQETLYWLAQPGIRESIAEADADIASGRTYGEDEIRAEFGVPRRPH:MPYTVRFTTTARRDLHKLPPRILAAVVEFAFGDLSREPLRVGKPLRRELAGTFSARRGTYRLLYRIDDEHTTVVILRVDHRADIYRR
```

Rules:

- `.csv` uses comma separation and `.tsv` uses tab separation.
- The parser uses string dtype, so keep IDs and paths explicit.
- `sequence` is uppercased and split on `:`. One chain is returned as a string; multiple chains are returned as a list.
- CSV/TSV parsing requires `pandas` to be importable.
- `a3mpath` and `templatepath` are returned as paths; they are not deeply validated by lightweight parsing alone.

## A3M files and directories

Supported suffix is `.a3m`.

```text
>101
YYDPETGTWY
>hit_1
YYDPETGTWY
```

Rules:

- A single `.a3m` file uses the file stem as the job name.
- The first FASTA/A3M sequence is the query sequence.
- The full file text is returned as a single-item `a3m_lines` list.
- Empty A3M files raise `ValueError` when provided as a single file and are logged/skipped when found in a directory.
- A3M content can include lowercase insertions and gap characters; do not normalize away lowercase letters unless a downstream tool explicitly asks for aligned uppercase sequences only.

## Directory inputs

Directories may contain `.a3m`, `.fasta`, `.faa`, `.fa`, `.pdb`, and `.cif` files. Other files are ignored with a warning. In the current parser, PDB/mmCIF directory entries still require AlphaFold's `protein` helper to be importable and are best preflighted as standalone files when debugging structure-derived sequence extraction.

Behavior:

- Files are visited in sorted filename order before optional query sorting.
- Directory FASTA/A3M job names use file stems, not FASTA headers.
- Empty FASTA files are logged and skipped; an empty standalone A3M raises.
- Duplicate unsafe names can collide later after sanitization. For example, `A:B.fasta`, `A/B` from a header, and `A B.fasta` may all become similar sanitized names in prediction outputs.
- For mixed A3M/FASTA directories, expect A3M entries to carry `a3m_lines` and FASTA entries to require MSA generation unless running single-sequence or precomputed-MSA workflows.

## Query sorting

`get_queries(input_path, sort_queries_by="length")` supports:

- `length`: default; sort ascending by concatenated sequence length.
- `msa_depth`: sort deepest A3M first by counting header lines in the first A3M block.
- `random`: shuffle query order.
- Any other value leaves the parser's current order unchanged in practice; prefer an explicit validator option such as `--sort none` only in wrapper scripts.

## AF3 non-protein molecule syntax

For AlphaFold3-compatible JSON workflows, ColabFold can encode non-protein components in FASTA complex strings using `molecule_type|sequence|(copies)`. Supported molecule types are `dna`, `rna`, `ccd`, and `smiles`.

```text
>complex_with_atp
FIRSTPROTEIN:SECONDPROTEIN:ccd|ATP|2
```

Equivalent explicit copies:

```text
>complex_with_two_atp
FIRSTPROTEIN:SECONDPROTEIN:ccd|ATP:ccd|ATP
```

SMILES caveat:

- Colons separate chains/components in ColabFold input.
- Aromatic-bond colons inside SMILES must be written as semicolons in FASTA input.
- `classify_molecules` converts semicolons back to colons for `smiles|...` entries.

Bad:

```text
>bad_ligand
PROTEINSEQ:smiles|c1cc:cc1
```

Good:

```text
>good_ligand
PROTEINSEQ:smiles|c1cc;cc1
```

Additional assumptions:

- Molecule type matching is case-insensitive after input uppercasing, but keep lowercase prefixes in docs and user-facing files for readability.
- Copy counts must parse as integers.
- Only protein sequences receive MMseqs2-based MSAs; non-protein components are represented for AF3 JSON workflows and may require AF3-side handling.

## A3M serialization header

`msa_to_str(unpaired_msa, paired_msa, query_seqs_unique, query_seqs_cardinality)` serializes complex MSA state with a first line:

```text
#<unique_lengths_comma_separated>\t<cardinalities_comma_separated>
```

Example for two unique chains where the first appears twice and the second appears once:

```text
#8,4	2,1
```

The serialized body combines paired and/or padded unpaired A3M blocks. Keep this header intact when moving precomputed complex MSAs between workflows; deleting it can make a complex look like a single-chain A3M.

## PDB and mmCIF input helpers

ColabFold can derive sequences from `.pdb` and `.cif` inputs when AlphaFold dependencies are installed. The lightweight `pdb_to_string(pdb_file, chains=None, models=None)` helper also filters PDB text:

- `chains` may be a chain ID, comma-separated chain IDs, or a list.
- `models` may be an integer or list of model numbers.
- Modified residues listed by ColabFold are converted to their standard residue names.
- Alternate placements are de-duplicated by model, chain, residue, and atom.
- Non-convertible heteroatoms are not treated as protein residues for template-style sequence extraction.

For template preparation and prediction-time use of PDB/mmCIF files, route to batch prediction or relaxation/output guidance as appropriate; this sub-skill owns only safe input interpretation and preflight checks.
