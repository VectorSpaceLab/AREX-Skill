# FASTA and Entity Rules

Chai reads a FASTA-like file where each record represents one molecular entity in the complex. The parser stores each record as `Input(sequence, entity_type, entity_name)`, then inference builds chains from those inputs.

## Header Grammar

Supported record headers are:

| Entity | Header forms | Sequence payload |
| --- | --- | --- |
| Protein | `>protein|chainA`, `>protein|name=chainA` | One-letter amino-acid sequence with optional modified residues in brackets/parentheses. |
| Ligand | `>ligand|lig1`, `>ligand|name=lig1` | SMILES string, including bracketed charged ions such as `[Mg+2]`. |
| DNA | `>dna|dna1`, `>dna|name=dna1` | Nucleotide letters expected to be compatible with DNA (`A`, `C`, `G`, `T` for standard bases). |
| RNA | `>rna|rna1`, `>rna|name=rna1` | Nucleotide letters expected to be compatible with RNA (`A`, `C`, `G`, `U` for standard bases). |
| Glycan | `>glycan|gly1`, `>glycan|name=gly1` | Manual glycan string; use the restraints/glycans sub-skill for bond and branch semantics. |

Header details:

- The first field before `|` is case-insensitive after stripping whitespace and must be one of `protein`, `ligand`, `rna`, `dna`, or `glycan`.
- A label field is required. `>protein` raises `label is not provided`.
- A single bare label field becomes the entity name, so `>protein|A` and `>protein|name=A` both name the entity `A`.
- Only one label field is supported. Extra fields such as `>protein|name=A|use_esm=true` are rejected by the current parser even though a code comment mentions possible future use.
- If the label uses `name=...`, the field name must be exactly `name`.
- Entity names must be unique before inference constructs a feature context.

## Sequence Rules

### Proteins and Modified Residues

Protein records accept normal one-letter amino-acid strings and bracketed modified residues. The same modified-FASTA tokenizer is also used for DNA/RNA compatibility checks.

Examples:

```fasta
>protein|name=kinase
MKWVTFISLLFLFSSAYSRGVFRR
>protein|name=phosphopeptide
AAA(SEP)AAA
>protein|name=multi_modified
(KCJ)(SEP)(PPN)(B3S)(BAL)(PPN)KX(NH2)
```

Important details:

- Modified residue tokens can use parentheses or square brackets, but each modification token must contain more than one character.
- Unclosed brackets, nested/double-open brackets, empty tokens `()`, and single-character modified tokens such as `(K)` are invalid.
- Single unbracketed characters must be ASCII letters. Unknown protein letters map through Chai's residue table where possible and may become `UNK`.
- A protein sequence containing `U` is not considered a likely protein by the heuristic because `U` is treated as an RNA-compatible base; if this is an intentional protein residue, expect a warning and inspect downstream behavior carefully.

### DNA and RNA

Standard DNA and RNA records should use one-letter nucleic-acid strings:

```fasta
>dna|name=primer
ACGACTAGCAT
>rna|name=guide
ACUGACG
```

Chai maps DNA bases to `DA`, `DC`, `DG`, `DT` and RNA bases to `A`, `C`, `G`, `U`. Unknown nucleic-acid letters are converted to unknown residue names (`DX` for DNA and `X` for RNA). Short strings containing only `A/C/G/T` or `A/C/G/U` can be compatible with several entity types, so trust the explicit header and review warnings.

### Ligands

Ligands are passed as SMILES strings and tokenized through Chai's ligand/conformer path:

```fasta
>ligand|name=palmitate
CCCCCCCCCCCCCC(=O)O
>ligand|name=magnesium
[Mg+2]
```

Important details:

- Chai identifies ligand entity identity from the SMILES string itself because ligand residues share a generic `LIG` residue name.
- Repeating the same SMILES with different entity names creates multiple ligand chains/symmetry copies but one ligand entity identity.
- Different SMILES strings for the same chemistry may be treated as distinct ligand entities.
- Malformed SMILES can survive FASTA parsing and then be dropped during `load_chains_from_raw` tokenization. Use the bundled validator's `--tokenize` mode when ligand syntax is risky.
- Bare metal symbols such as `Zn` can be malformed for tokenization; use charged/bracketed forms such as `[Zn+2]` when appropriate.

### Glycan Header Scope

Basic glycan records use the same required-name header rule:

```fasta
>glycan|name=nag_chain
NAG(4-1 NAG)
```

The input-data-formats sub-skill only covers the presence and naming of the `glycan|...` FASTA record. Use `../restraints-glycans/SKILL.md` for glycan branch syntax, CCD residue expectations, leaving atoms, and protein-glycan covalent restraint rows.

## Entity Names, Entities, and Chains

Chai separates several related concepts:

- `entity_name` is the name from the FASTA header.
- `entity_id` groups identical molecular entities. Duplicate protein sequences share one entity ID; duplicate ligand SMILES share one entity ID.
- Asymmetric chain/symmetry IDs distinguish copies. Two identical protein records with names `A` and `B` become two chains/symmetry copies of one entity.
- `subchain_id` is the chain-like identifier used by restraints and output naming behavior.

Unique entity names are still required even when sequences are identical. For example:

```fasta
>protein|name=A
RKDES
>protein|name=B
RKDES
```

This is valid and represents two copies. Reusing `name=A` for both records fails inference setup.

## Chain Naming Modes

By default, Chai assigns automatic chain/subchain IDs in input order: `A`, `B`, ..., `Z`, `AA`, `AB`, and so on. This mode is used when `fasta_names_as_cif_chains=False` in `run_inference` or `entity_name_as_subchain=False` in `load_chains_from_raw` / `make_all_atom_feature_context`.

When `fasta_names_as_cif_chains=True`, Chai uses FASTA entity names as chain/subchain IDs for parsing restraints and writing output CIF chain names. The lower-level equivalent is `entity_name_as_subchain=True`.

Choose deliberately:

| Need | Recommended mode | Consequence |
| --- | --- | --- |
| Simple fold with no restraints and no chain-name constraints | Automatic IDs | Records map to `A`, `B`, `C` by accepted order. |
| Restraints written against record names like `receptor` and `ligand` | FASTA names as chains | Pass `fasta_names_as_cif_chains=True`; restraint chain names must match entity names. |
| Restraints written against automatic `A`/`B`/`C` | Automatic IDs | Keep `fasta_names_as_cif_chains=False`; restraint chain names must match generated order. |
| Output CIF must preserve names like `H`, `L`, `antigen` | FASTA names as chains | Ensure names are unique, ASCII, and short enough for Chai's padded chain-code path. |

Practical caution: Chai converts subchain IDs into fixed-length tensor codes in some paths, commonly padded to length 4. Prefer short ASCII entity names when they will be used as chain IDs, especially with restraints or custom contexts.
