# MSA and template loading

This reference covers the local feature loaders used during `PDBInput` conversion.
The loaders do not perform database searches or downloads. They consume files
that have already been acquired and indexed into the naming layouts below.

## MSA directory layout

For an ordinary PDB input with `file_id` such as
`7a4d-assembly1` and chain `A`, the loader searches:

```text
<msa_dir>/7a4d-assembly1A_*.a3m
<msa_dir>/7a4d-assembly1A_*.a3m.gz
```

The glob is `file_id + chain_id + "_*.a3m*"`; a directory may contain several
such files. The first FASTA/A3M sequence must be the query and, after parsing,
its ungapped aligned length must equal the polymer sequence length derived from
the structure. Ligands are not represented in the alignment and are inserted
as unknown residue positions by feature construction.

For a distillation input, the loader searches every associated PDB ID under
an AFDB-style directory pattern:

```text
<msa_dir>/<pdb_id-without--assembly1>_*/a3m*
```

The associated IDs come from `PDBDistillationDataset`'s mapping, not from a
filename guess. Keep the accession-to-PDB mapping and the MSA directory from
the same data snapshot.

The repository's small checked-in examples use both plain `.a3m` and gzip
`.a3m.gz`. The loader detects gzip from the file header, not only from the
suffix. A validator may check suffixes and existence; only the package parser
can establish that the content is a valid A3M.

## A3M parsing and MSA features

`msa_parsing.parse_a3m(a3m_string, msa_type)` returns an immutable `Msa` with:

- `sequences`: aligned sequences with lowercase insertion characters removed;
- `deletion_matrix`: one deletion count per query-aligned position per row;
- `descriptions`: the FASTA headers without `>`; and
- `msa_type`: `protein`, `rna`, `dna`, or `ligand`.

The first sequence is required to be the query by convention. Every MSA field
must have the same number of rows. A malformed or empty FASTA should be
stopped and diagnosed; do not repair sequence lengths by padding them in a
layout manifest.

`load_msa_from_msa_dir` constructs a length-one query-only MSA before looking
for files. For each chain it:

1. derives the polymer query sequence from unique residue indices;
2. parses every matching file with the chain's majority chemical type;
3. retains only files whose first sequence length equals the expected query
   length;
4. concatenates the accepted MSAs, dropping duplicate sequences within each
   file; and
5. installs the query-only MSA if no valid file remains or a file fails to
   parse. Verbose mode logs the missing or failed pattern.

This fallback is intentional and usable for a bounded input, but it is not a
claim of evolutionary coverage. Record `msa_source=query-only` when it is
selected. In particular, a present directory with no matching files is not
the same evidence as a successfully parsed alignment.

`max_msas_per_chain` is an alignment-row cap. When multiple chain files are
available, the loader divides the cap by the number of accepted files and
truncates each file to that proportional allocation. The `PDBInput` path uses
normal (first-row) truncation; the lower-level loader also exposes a random
truncation option, but it is not enabled by ordinary `PDBInput` conversion.
`max_num_msa_tokens` is a structure-level guard: if `num_tokens *
max_msas_per_chain` exceeds it, `PDBInput` discards the directory for that
example and uses one query row per chain.

Feature construction deduplicates rows, makes deletion and profile features,
adds MSA masks, and pads chain feature arrays to a common alignment depth.
The model-facing fields are named `msa`, `msa_mask`/`msa_row_mask`,
`additional_msa_feats`, and `additional_token_feats` after conversion. The
additional MSA channels are `has_deletion` and transformed deletion value;
additional token channels contain the per-position profile and mean deletion.
The MSA is one-hot encoded with the package's combined protein/RNA/DNA/unknown
vocabulary. Its final residue/token axis must equal the biomolecule token axis;
a mismatch is a hard assertion during conversion.

## MSA pairing semantics

For each chain, species identifiers are extracted from headers. Ordinary PDB
MSAs use the repository's tab-separated alignment-header convention; the
query row is tagged `-1`. Distillation MSAs use the UniProt-style identifier
parser. Unrecognized headers produce an empty species identifier and are not
reliable pairing evidence.

Chains with more than one entity attempt pairing. Rows for a species present
in only one chain are not paired. A species with more than 100 candidate
sequences is skipped by the pairing helper. Rows are sorted by sequence
similarity to the respective query, then paired across chains; absent chain
rows use a padding row. Homomeric chains are first merged into dense features.
Paired and unpaired rows are then concatenated, with the configured maximum
cap. If pairing raises an exception, the loader logs it in verbose mode and
continues without paired features. Do not interpret unpaired fallback as an
alignment failure if the individual MSA is valid.

## Template directory layout

For an ordinary PDB input, the loader searches chain-specific M8 files:

```text
<templates_dir>/<file_id><chain_id>_*.m8
```

For distillation it searches HHR files under associated PDB directories:

```text
<templates_dir>/<pdb_id-without--assembly1>_*/hhr/*.hhr
```

Each hit names a template chain, and the corresponding local structure is
looked up under the supplied `mmcif_dir` as:

```text
<mmcif_dir>/<template_id[1:3]>/<template_id>-assembly1.cif
```

The `mmcif_dir` is derived from the ordinary input's mmCIF parent hierarchy,
or is explicitly supplied by `distillation_template_mmcif_dir` for
 distillation. This is a local lookup; no remote template is fetched.

## M8/HHR filtering and limits

`template_parsing.parse_m8` and `parse_hhr` apply the same logical filters:

- reject a hit whose template ID contains any part of the query ID;
- keep identity strictly greater than `0.3` and strictly less than `0.95`;
- require a positive alignment column/length; and
- require template span `Template End - Template Start >= 9`, which means at
  least ten positions under the parser's inclusive interpretation.

M8 identity and alignment length are read from tab-separated columns. HHR
identity is derived from `Cols / Query HMM end`, and the template HMM range is
parsed from the range field. Rows are limited to `max_templates` first, then
selected to `num_templates`; random selection occurs only when the explicit
`randomly_sample_num_templates=True` option is used. A candidate whose local
mmCIF is missing, cannot be parsed, has no selected atoms, or is newer than
`template_cutoff_date` is skipped.

The cutoffs installed by `pdb_input_to_molecule_input` are:

| Mode | Template release-date cutoff |
|---|---|
| ordinary training | query structure release date minus 60 days |
| distillation training | `2018-04-30` |
| inference (ordinary or distillation) | `2021-01-12` |

A template with release date later than the cutoff is rejected. The cutoff is
not a guarantee that the template search was complete; it only describes the
local candidates considered.

## Kalign and template features

`make_template_features` aligns each selected single-chain template to the
query with the configured local Kalign binary, then extracts restype,
pseudo-beta mask, backbone-frame mask, distance-bin, and unit-vector features.
Inter-chain template pair features are zeroed by block-diagonal assembly. The
usual model configuration uses `dim_template_feats=108`; the resulting
feature tensor has the form `[template, token, token, feature]` and a Boolean
`template_mask`.

Kalign is an external executable. The wrapper requires every sequence to be at
least six residues long, writes temporary input/output files, and raises on a
non-zero process exit. `_realign_pdb_template_to_query` also requires the
binary path to exist and rejects alignments with less than 10% matching
residues relative to the shorter sequence. A missing path, short chain, bad
binary, or low-identity alignment is a real template limitation.

Missing templates or a missing Kalign path normally produce zero/dummy
features and a false mask for the affected slots. `make_template_features`
can instead raise when its `raise_missing_exception=True` option is used, but
the directory loader does not select that strict mode. A `PDBInput` template
budget (`max_num_template_tokens`) can skip curation for the whole example
when `num_tokens * num_templates_per_chain` exceeds the cap. Record whether
templates were `loaded`, `dummy/missing`, `budget-skipped`, or `alignment-skipped`.

## Safe local preflight

Before conversion, check without importing the package:

1. each structure path exists and ends in `.cif` or `.cif.gz`;
2. each MSA directory contains only expected `.a3m`/`.a3m.gz` candidates (or
   is explicitly allowed to be empty for query-only fallback);
3. each template directory contains `.m8` or `.hhr` candidates and the
   associated local template mmCIF tree exists;
4. the MSA/template filename stem uses the exact `file_id` and chain IDs; and
5. the configured caps, cutoff date, and crop are internally consistent.

Use `scripts/validate_data_layout.py` for these deterministic checks. It does
not parse biological content, run Kalign, read the CCD, download anything, or
rewrite a layout.
