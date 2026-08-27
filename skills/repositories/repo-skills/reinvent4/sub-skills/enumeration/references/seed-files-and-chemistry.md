# Seed Files and Chemistry Checks

Seed files are small text inputs that control either peptide enumeration or seed-based generator sampling. Enumeration itself uses peptide templates plus an amino-acid library. LibInvent, LinkInvent, Mol2Mol, and PepInvent seed files are sampling inputs, but their chemistry and attachment-point failures often surface while designing enumeration/scoring workflows.

## File Conventions

| File kind | Typical file | Expected rows | Main checks |
| --- | --- | --- | --- |
| Enumeration peptides | `peptides.smi` | One peptide template per non-comment row, first column read | `?` mask count is 1 or 2; `|` separates fragments; RDKit can parse after masks are filled. |
| Amino-acid library | `amino_acids.csv` | CSV with name and SMILES columns | `aa_names_column` and `smiles_column` exist; names are non-empty and unique; fragment SMILES are non-empty. |
| LibInvent scaffolds | `scaffolds.smi` | One scaffold per non-comment row | Attachment points use `*`, `[*]`, or labels like `[*:0]`; common scaffold rows have two points. |
| LinkInvent warheads | `warheads.smi` | One warhead pair per non-comment row | Exactly one `|` separates the two warheads; each side has one attachment point. |
| Mol2Mol seeds | `mol2mol.smi` | One compound per row, optional label columns | First column is a parseable molecule; keep row counts small for memory-heavy jobs. |
| PepInvent seeds | `pepinvent.smi` | One masked peptide row per non-comment row | `?` masks and `|` separators are present; mask count matches the intended task. |

Comment lines beginning with `#` and blank lines are safe to include. For `.smi` files, REINVENT4 readers generally use the first column as the SMILES-like payload; labels in later tab-separated columns are tolerated for Mol2Mol-style inputs but are not part of the molecule.

## Attachment-Point Markers

REINVENT4 library-design utilities recognize attachment points expressed as wildcard atoms:

- Bare wildcard: `*`
- Bracketed wildcard: `[*]`
- Numbered attachment point: `[*:0]`, `[*:1]`, `[*:2]`

Numbered attachment points are useful because scaffold and decoration joins match labels. Internal utilities can add, remove, and normalize attachment-point numbers, but static seed files should still be clear and unambiguous.

Recommended checks:

- A LibInvent scaffold should have at least one attachment point; many standard scaffold-decoration priors expect two.
- A LinkInvent warhead row should contain exactly one pipe separator and one attachment point on each side.
- A decoration or warhead fragment with more than one attachment point is usually invalid for a single join.
- Do not put two attachment points on the same atom when reaction-filter compatibility matters; internal comments note this can create label ambiguity.
- Prefer bracketed/numbered markers like `[*:0]` over bare `*` when humans need to inspect or debug joins.

## Example Shapes

LibInvent scaffold rows:

```text
[*:0]Cc2ccc1cncc(C[*:1])c1c2
[*:0]Cc2cnc1cncc(C[*:1])c1c2
```

LinkInvent warhead row:

```text
Oc1cncc(*)c1|*c1ccoc1
```

Mol2Mol row with optional tab-separated label:

```text
O=S(=O)(c1cccc2cnccc12)N1CCCNCC1	CHEMBL38380
```

PepInvent masked peptide row:

```text
?|N[C@@H](CO)C(=O)|?|N[C@@H](Cc1ccc(O)cc1)C(=O)
```

Enumeration peptide row:

```text
N[C@@H](CS)C(=O)|?|N[C@@H](C)C(=O)|?|N[C@@H](C)C(=O)O
```

Amino-acid library CSV:

```csv
Name,SMILES
R,N=C(N)NCCC[C@H](N)C(=O)
H,N[C@@H](Cc1c[nH]cn1)C(=O)
A,N[C@@H](C)C(=O)
```

## Enumeration Library Details

- Use `amino_acid_library_file` in the config to point to the library CSV.
- Use `aa_names_column` for the amino-acid identifier column. These identifiers are what the runtime enumerates and records in `Amino_Acids`.
- Use `smiles_column` for the fragment SMILES column. The column name `RDKit_SMILES (REINVENT)` is reserved and should not be used here.
- Whitespace around names and SMILES is stripped by the runtime.
- Duplicate amino-acid names collapse when the library is converted to a dictionary; make names unique to avoid silently losing variants.
- Empty names or empty SMILES should be treated as errors before running.

## Optional RDKit Checks

The bundled validator can import RDKit when it is available. Optional RDKit checks are conservative:

- For scaffold and warhead rows, remove wildcard atoms before parsing when possible or parse fragments as-is when RDKit accepts them.
- For Mol2Mol rows, parse the first column directly.
- For PepInvent/enumeration masked rows, static parsing is limited because `?` placeholders are not valid SMILES. Validate mask/separator shape first, then rely on a small enumeration smoke run to prove the full filled peptide chemistry.

Missing RDKit is not itself a seed-file failure. Use string checks to catch separator, column, and attachment-point mistakes before escalating to a full REINVENT4 run.
