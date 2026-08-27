# Restraints and Glycans

This reference is self-contained guidance for Chai-1 version `0.6.1` restraint and glycan inputs. It covers the restraint CSV consumed through `constraint_path`, not full FASTA authoring, MSA/template setup, or model execution.

## Restraint CSV Schema

Chai parses restraint files as CSV tables. Include these columns:

| Column | Required meaning |
| --- | --- |
| `restraint_id` | Unique string identifier for each row. Duplicate values fail schema validation. |
| `chainA` | Chain/subchain identifier for partner A. Required. |
| `res_idxA` | Partner A residue and optional atom, or blank for pocket chain-level partner A. |
| `chainB` | Chain/subchain identifier for partner B. Required. |
| `res_idxB` | Partner B residue and optional atom. Required for contact and pocket rows; atom-only is common for ligand/glycan covalent rows. |
| `connection_type` | One of `contact`, `pocket`, or `covalent`. |
| `confidence` | Float in `[0.0, 1.0]`; defaults to `1.0` when blank. Current model logic does not use it for manual restraints. |
| `min_distance_angstrom` | Non-negative float; present for format stability. Current manual restraint logic does not use it for contact/pocket feature values or covalent bonds. |
| `max_distance_angstrom` | Non-negative float. Contact and pocket rows use this as the distance threshold. |
| `comment` | Free text for humans; parsed but not used by the model. |

The parser accepts any column order that includes these names. Chai's bundled writer emits `restraint_id` last, while docs often show it first; both are valid CSV layouts because parsing is by column name.

## Chain Naming Rule

Restraint `chainA` and `chainB` must match how Chai builds subchain identifiers for the FASTA input:

- Default inference (`fasta_names_as_cif_chains=False`): chains are automatic `A`, `B`, `C`, ... in FASTA record order.
- FASTA-name mode (`fasta_names_as_cif_chains=True`): chains use the FASTA entity names from headers such as `>protein|heavy` and `>glycan|glycan1`.

A mismatch can parse cleanly but silently produce all-null contact/pocket features or later fail atom lookup for covalent bonds. Decide chain naming before writing restraints and keep the FASTA, CSV, and inference option aligned.

## Residue and Atom Notation

`res_idxA` and `res_idxB` use these forms:

- `A219`: residue one-letter code plus 1-based position. The parser stores `A` and position `219`.
- `A219@CA`: residue plus atom name. Use this for atom-specific covalent bonds or expert atom-specific contacts.
- `@C1`: atom-only form. With no residue prefix, Chai treats the token position as the first residue/token of that partner. This is useful for single-token ligands and root glycan rings.
- blank: allowed only where the row type explicitly uses a chain-level partner, such as pocket `res_idxA`.

Residue positions are 1-based in CSV. Chai converts them to 0-based internally. If a residue letter is supplied, downstream loading checks it against the FASTA/token residue name for contact, pocket, and covalent rows. Malformed strings such as `A219@`, `@@C1`, or an all-empty atom/residue field where one is required fail before inference.

## Connection Type Semantics

### Contact

A `contact` row constrains a specific residue or atom on partner A to a specific residue or atom on partner B. Use it for residue-residue interface hints.

```csv
chainA,res_idxA,chainB,res_idxB,connection_type,confidence,min_distance_angstrom,max_distance_angstrom,comment,restraint_id
A,C387,B,Y101,contact,1.0,0.0,5.5,protein-heavy,restraint_1
C,I32,A,S483,contact,1.0,0.0,5.5,protein-light,restraint_2
```

Parser-level rules:

- `res_idxA` or `atom_nameA` must be present.
- `res_idxB` or `atom_nameB` must be present.
- Atom suffixes are parsed, but ordinary residue-level contact rows usually omit atoms.

Feature-loading rules:

- The residue one-letter codes must match the corresponding FASTA residues.
- The chain identifiers must match Chai's subchain identifiers.
- `max_distance_angstrom` becomes the contact distance threshold.

### Pocket

A `pocket` row says any residue in chain A may be near the specified token in chain B. It is asymmetric and coarser than a contact restraint.

```csv
chainA,res_idxA,chainB,res_idxB,connection_type,confidence,min_distance_angstrom,max_distance_angstrom,comment,restraint_id
B,,A,C387,pocket,1.0,0.0,5.5,protein-heavy,restraint_0
C,,A,S483,pocket,1.0,0.0,5.5,protein-light,restraint_1
```

Rules:

- `res_idxA` must be blank.
- `res_idxB` must specify a token such as `C387`.
- Do not specify atom suffixes for pocket rows.
- `max_distance_angstrom` becomes the pocket distance threshold.

### Covalent

A `covalent` row creates an atom-level bond between two partners. Use it for protein-glycan, protein-ligand, and other non-canonical bonds.

```csv
chainA,res_idxA,chainB,res_idxB,connection_type,confidence,min_distance_angstrom,max_distance_angstrom,comment,restraint_id
A,N437@N,B,@C1,covalent,1.0,0.0,0.0,protein-glycan,bond1
A,N445@N,C,@C1,covalent,1.0,0.0,0.0,protein-glycan,bond2
```

Rules:

- Both sides must include atom names, for example `N437@N` and `@C1`.
- If a residue prefix is omitted, Chai targets token position `1` on that chain.
- `confidence`, `min_distance_angstrom`, and `max_distance_angstrom` are parsed but ignored for covalent bond creation.
- Contact and pocket restraints are handled as restraint features; covalent restraints are handled as atom covalent-bond indices.

For a non-glycan ligand, use atom names assigned by Chai/RDKit for the ligand conformer. One observed protein-ligand pattern is:

```csv
chainA,res_idxA,chainB,res_idxB,connection_type,confidence,min_distance_angstrom,max_distance_angstrom,comment,restraint_id
A,C217@SG,B,@S1,covalent,1.0,0.0,0.0,protein-ligand,bond1
```

## Glycan FASTA Syntax

Chai uses `>glycan|name` FASTA entries for manual glycans. The sequence is an abbreviated glycan string made from three-character CCD codes and glycosidic-bond branch syntax.

Single sugar:

```fasta
>protein|example-protein
...N...
>glycan|example-single-sugar
NAG
```

Two-ring glycan:

```fasta
>protein|example-protein
...N...
>glycan|example-dual-sugar
NAG(4-1 NAG)
```

Interpretation:

- The leading CCD code is the root sugar.
- Parentheses attach a child sugar to the immediately preceding parent sugar or to the root sugar in the current branch.
- `4-1` means the parent `O4` atom bonds to the child `C1` atom.
- Chai accepts bond digits `1` through `6` on each side.
- Whitespace is ignored by the glycan parser.

Longer linear and branched forms:

```fasta
>glycan|linear
NAG(4-1 NAG(4-1 NAG(4-1 NAG)))

>glycan|branched
NAG(4-1 NAG(4-1 BMA(3-1 MAN)(6-1 MAN)))
```

Glycan parser implications:

- Each CCD code becomes one glycan residue with 1-based label sequence numbers.
- `_glycan_string_to_sugars_and_bonds` parses CCD chunks matching three uppercase letters/digits, such as `NAG`, `MAN`, `FUC`, `BMA`, or `99K`.
- Unbalanced parentheses, malformed bond chunks, unsupported characters, or missing residues fail validation.

## Protein-Glycan Bond Rows

For a protein glycosylated at asparagine and a glycan chain whose root sugar is first in that glycan entry, connect the protein atom to the glycan root atom:

```csv
chainA,res_idxA,chainB,res_idxB,connection_type,confidence,min_distance_angstrom,max_distance_angstrom,comment,restraint_id
A,N436@N,B,@C1,covalent,1.0,0.0,0.0,protein-glycan,bond1
```

Use `chainB` equal to the glycan subchain identifier. In default chain mode, if the FASTA records are protein then glycan, `chainB` is usually `B`. In FASTA-name mode, use the glycan entity name, for example `example-dual-sugar`.

## Leaving Atoms and Non-Glycan Ligands

Chai automatically attempts to remove leaving hydroxyl groups for glycan sugar rings when bonds are formed. This behavior is specific to glycan rings. For non-glycan covalent ligands, provide a SMILES string that already omits leaving atoms, or expect atom lookup/geometry problems.

Do not model modified amino acids with covalent restraint rows when a CCD code exists for the residue. Put the CCD code directly in the protein sequence using modified residue syntax, such as `RKDES(MSE)EES`, and reserve covalent rows for bonds that are not already encoded by an input residue.

## Minimal Authoring Checklist

- Pick the chain naming mode and document it next to the CSV.
- Verify every `restraint_id` is unique.
- Use `contact` for residue-residue restraints and fill both residue fields.
- Use `pocket` for chain-to-token restraints and leave `res_idxA` blank.
- Use `covalent` for atom-level bonds and include `@atom` on both sides.
- Keep residue positions 1-based.
- For glycan chains, validate the FASTA glycan string and use `@C1`, `@C2`, etc. on the glycan side when targeting the root sugar.
- Run the bundled validator before invoking Chai-1 inference.
