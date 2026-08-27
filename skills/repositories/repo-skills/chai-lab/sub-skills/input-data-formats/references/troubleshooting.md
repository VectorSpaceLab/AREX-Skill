# Input FASTA Troubleshooting

Use this guide when Chai rejects a FASTA file, logs sequence-type warnings, silently loses a ligand during tokenization, or maps restraints/output chains to unexpected names.

## Header and Name Failures

### `label is not provided`

Cause: A record header has only the entity type, such as `>protein`.

Fix: Add a required label field:

```fasta
>protein|name=receptor
MKWVTFISLL
```

### `is not a valid entity type`

Cause: The first header field is not one of Chai's accepted input types.

Fix: Use one of `protein`, `ligand`, `dna`, `rna`, or `glycan` before the first `|`.

### `Unsupported inputs: desc=...`

Cause: The header has too many `|` fields, such as `>protein|name=A|use_esm=true`.

Fix: Keep only the entity type and one name field. Put inference choices in CLI/API arguments, not FASTA headers.

### `field_name == "name"` assertion

Cause: A keyed label uses a key other than `name`, such as `>protein|chain=A`.

Fix: Use `>protein|name=A`, or use the bare form `>protein|A`.

### Duplicate entity names

Cause: Inference context construction counts FASTA `entity_name` values and rejects duplicates, even when the duplicated records have identical sequences.

Fix: Rename each chain copy uniquely:

```fasta
>protein|name=A
RKDES
>protein|name=B
RKDES
```

Identical sequences still share entity identity internally, but they need distinct record names.

## Sequence-Type Warnings

### `Provided sequence is likely ..., not ...`

Cause: Chai's heuristic sees the sequence as compatible with a different type than the header. This is common for short nucleic acids and amino-acid-like sequences.

Fix:

- Confirm the header is intentional.
- For DNA, prefer standard `A/C/G/T`; for RNA, prefer `A/C/G/U`.
- For proteins with unusual residues, use explicit modified-residue syntax where possible.
- If a protein includes `U`, inspect carefully because the heuristic excludes `U`-containing records from likely protein matches.

### Invalid or malformed modified-residue syntax

Symptoms: Parser returns no possible polymer type, or later chain construction raises an assertion for incorrect FASTA.

Fix:

- Use `AAA(SEP)AAA` or `[SEP]`-style multi-character modified tokens.
- Do not use empty `()`, single-character `(K)`, nested brackets, or unclosed brackets.
- Keep unbracketed polymer symbols to single ASCII letters.

## Ligand and SMILES Problems

### FASTA parses but ligand disappears during tokenization

Cause: `read_inputs` only parses the record and applies broad syntax heuristics. `load_chains_from_raw` tokenizes ligands later and drops entries that fail tokenization.

Fix:

- Run `python scripts/validate_chai_fasta.py --tokenize input.fasta` before folding.
- Validate the SMILES with chemistry tooling when available.
- Use bracketed charged ions, such as `[Mg+2]` and `[Zn+2]`, instead of bare metal names.

### Repeated ligands merge unexpectedly

Cause: Chai identifies ligand entity identity from the SMILES string, not from the FASTA name. Repeating the same SMILES creates multiple chains/copies of one ligand entity.

Fix: This is expected for symmetric copies. If the ligands are intended to be chemically distinct, ensure their SMILES strings differ in the intended way.

## Chain Naming and Restraints

### Restraints do not affect the model

Cause: Restraint chain names do not match the chain naming mode used for input parsing. Chai can parse restraints but produce all-null restraint features when names mismatch.

Fix:

- If restraint rows use automatic `A`, `B`, `C` chain names, keep `fasta_names_as_cif_chains=False`.
- If restraint rows use FASTA names such as `receptor` and `ligand`, pass `fasta_names_as_cif_chains=True` to `run_inference` or `entity_name_as_subchain=True` in lower-level context construction.
- Preserve FASTA record order when using automatic IDs.

### Output CIF chain names are unexpected

Cause: Default inference writes output chain names as automatic `A`, `B`, `C`, ... regardless of FASTA entity names.

Fix: Pass `fasta_names_as_cif_chains=True` when output CIF chain names should match FASTA entity names. Keep those entity names unique and short ASCII strings.

### Chain-name mode fails with long or non-ASCII names

Cause: Chai tensor-encodes subchain IDs as ASCII and some paths pad to fixed length. Long names can fail assertions in lower-level paths.

Fix: For entity names that become chain IDs, prefer concise ASCII identifiers such as `A`, `B`, `H`, `L`, `R1`, or `lig1`.

## Total Length and Empty Input

### Too many input characters

Cause: `read_inputs(..., length_limit=N)` sums raw sequence/SMILES characters and raises when the total exceeds `N`.

Fix: Split oversized exploratory inputs, remove accidental pasted annotations, or raise the caller's validation limit if it is intentionally conservative.

### No inputs found

Cause: The FASTA file has no parseable records or the file path is wrong.

Fix: Confirm records start with `>` headers and run the bundled validator from the same environment that will run Chai.

## Cross-Skill Escalation

- Escalate to `../cli-inference/SKILL.md` for output directory, device, CUDA, model weight, ranking, and full `run_inference` issues.
- Escalate to `../msa-templates/SKILL.md` for MSA directory, `.aligned.pqt`, A3M conversion, and template hit matching.
- Escalate to `../restraints-glycans/SKILL.md` for restraint CSV schema, glycan branch syntax, covalent bonds, atom notation, and chain names inside restraint rows.
