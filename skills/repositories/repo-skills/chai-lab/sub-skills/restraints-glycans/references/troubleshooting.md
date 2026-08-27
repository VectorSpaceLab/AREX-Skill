# Troubleshooting Restraints and Glycans

Use this guide after reading `restraints-and-glycans.md`. Start with `python scripts/validate_restraints.py restraints.csv --fasta input.fasta` to catch cheap issues before model execution.

## Duplicate `restraint_id`

Symptom:

- Parser validation fails with a uniqueness/schema error for `restraint_id`.

Cause:

- Two or more rows reuse the same identifier.

Fix:

- Give every row a stable unique ID such as `contact_001`, `pocket_001`, `bond_glycan_001`.
- If constructing restraints programmatically, use `write_pairwise_table` to generate IDs and then rename only if necessary.

## Invalid `connection_type`

Symptom:

- Parser validation reports that `connection_type` is not in the allowed set.

Cause:

- Typos or unsupported labels such as `bond`, `distance`, `interface`, or uppercase variants.

Fix:

- Use exactly one of `contact`, `pocket`, or `covalent`.
- Keep `covalent` rows atom-specific; do not use `contact` for bond creation.

## Contact Row Fails Assertion

Symptom:

- Validation fails with `A should specify a token/atom` or `B should specify a token/atom`.

Cause:

- A `contact` row has a blank `res_idxA` or `res_idxB` without an atom-only notation.

Fix:

- Fill both sides with residue notation such as `C387` and `Y101`, or expert atom notation such as `C387@SG`.
- Use `pocket` instead if one side should mean an entire chain.

## Pocket Row Fails Assertion

Symptom:

- Validation fails with `A (chain-level) should NOT specify a token`, `B (token-level) should specify a token`, or `No atoms should be specified`.

Cause:

- `pocket` is asymmetric: side A is the whole pocket chain and side B is the token.

Fix:

- Leave `res_idxA` blank.
- Fill `res_idxB` with a residue token such as `C387`.
- Remove atom suffixes from both sides.

Correct pattern:

```csv
chainA,res_idxA,chainB,res_idxB,connection_type,confidence,min_distance_angstrom,max_distance_angstrom,comment,restraint_id
B,,A,C387,pocket,1.0,0.0,5.5,pocket near protein residue,pocket_001
```

## Malformed Residue Atom Notation

Symptom:

- Validation fails with `Invalid residue index` or a position conversion error.

Common causes:

- Trailing `@`, such as `A219@`.
- More than one `@`, such as `A219@CA@CB`.
- Empty atom-only field `@`.
- Zero or negative residue index, such as `A0`.
- Accidentally using three-letter amino-acid names in residue tokens, such as `ASN436@N`; Chai expects one-letter residue code plus index, such as `N436@N`.

Fix:

- Use `A219`, `A219@CA`, or `@C1` forms.
- Keep residue positions 1-based.
- For atom-only ligand/glycan sides, use `@atom` without a residue prefix.

## Chain-Name Mismatch

Symptom:

- CSV parser succeeds, but contact or pocket features appear all-null, covalent atom lookup fails, or restraints do not affect predictions.

Cause:

- Restraints use `A`/`B`/`C` while inference is using FASTA entity names, or restraints use entity names while inference is using automatic chain letters.

Fix:

- If `fasta_names_as_cif_chains=False`, use automatic chain letters by FASTA order.
- If `fasta_names_as_cif_chains=True`, use FASTA names from headers.
- Re-run the bundled validator with `--fasta` and either default mode or `--fasta-names-as-cif-chains` to catch obvious chain mismatches.

Example:

```fasta
>protein|heavy
...
>protein|light
...
```

- Default mode: restraints use `A` and `B`.
- FASTA-name mode: restraints use `heavy` and `light`.

## Residue Letter or Index Mismatch

Symptom:

- Parser validation succeeds, but feature loading fails or restraints are ignored.

Cause:

- The residue one-letter code or 1-based position does not match the FASTA sequence for that chain.

Fix:

- Count positions from 1, not 0.
- Check the one-letter residue at the requested position.
- Run the bundled validator with `--fasta`; it performs a lightweight check for protein, RNA, and DNA records when the chain and position are unambiguous.
- For modified residues and glycans, prefer Chai feature-building checks because residue tokenization can differ from raw character count.

## Covalent Row Missing Atom Names

Symptom:

- Feature loading fails with `Atoms must be provided for covalent bonds`.

Cause:

- A `covalent` row specified only residues, such as `N436` and blank/`NAG` side, without atom names.

Fix:

- Include `@atom` on both sides, for example `N436@N` and `@C1`.
- For protein cysteine ligand bonds, a common protein atom is `SG` in `C217@SG`.
- For glycan root sugar bonds, use root sugar atoms such as `@C1`.

## Covalent Atom Lookup Fails

Symptom:

- Feature loading fails with an assertion expecting a single atom but finding zero or multiple atoms.

Cause:

- Chain ID, residue index, residue name, or atom name does not identify exactly one atom in the tokenized Chai context.

Fix:

- Confirm chain naming mode first.
- Confirm residue positions are 1-based in the CSV.
- Use one-letter residue prefixes for protein residues.
- For glycan atom names, use ring atom names such as `C1`, `C2`, `O4`, matching the glycosidic bond syntax.
- For non-glycan ligands, verify Chai/RDKit atom names in the generated conformer before assuming names such as `S1` or `C1`.

## Glycan String Rejected

Symptom:

- FASTA/glycan validation fails for a `>glycan|...` sequence.

Common causes:

- CCD code is not three uppercase letters/digits.
- Parentheses are unbalanced.
- Bond notation is not one digit `1` through `6`, hyphen, one digit `1` through `6`.
- A branch lacks a child sugar after the bond.

Fix:

- Use examples such as `NAG`, `NAG(4-1 NAG)`, or `NAG(4-1 NAG(4-1 BMA(3-1 MAN)(6-1 MAN)))`.
- Remove unsupported separators; whitespace is optional but arbitrary punctuation is not.
- Validate with `scripts/validate_restraints.py --fasta input.fasta`.

## Glycan Covalent Bond Points to Wrong Ring

Symptom:

- Protein-glycan covalent setup parses but does not represent the intended attachment.

Cause:

- `@C1` without a residue prefix targets the first glycan token/residue. For a branched or multi-ring glycan, this is the root sugar.

Fix:

- Attach the protein to the intended root atom when using `@C1`.
- If targeting a later glycan residue is necessary, specify a residue token plus atom once you have confirmed how that glycan token is represented.
- Keep glycan internal bonds in the FASTA glycan string rather than as additional CSV rows unless you are intentionally overriding the default parser behavior.

## Non-Glycan Leaving Atoms

Symptom:

- A non-glycan covalent ligand has impossible valence/geometry or fails atom matching after adding a bond.

Cause:

- Chai's automatic leaving-atom removal is glycan-specific and targets glycan hydroxyl groups. It does not generally remove leaving atoms from arbitrary SMILES ligands.

Fix:

- Provide a non-glycan ligand SMILES string without the leaving atoms.
- If a modified amino acid has a CCD code, encode it directly in the FASTA sequence as a modified residue instead of adding a covalent row.
- Treat unusual non-glycan covalent ligands as expert cases that need atom-name inspection and likely manual chemistry review.

## Parser Passes but Inference Still Fails

Likely causes:

- `output_dir` is not empty.
- Device or model weights are unavailable.
- FASTA entity syntax is invalid or duplicate entity names are used.
- MSA/template options conflict with local inputs.
- The restraint row is schema-valid but fails feature-building checks.

Fix:

- Use this sub-skill for the restraint/glycan piece, then route full inference setup to `../cli-inference/SKILL.md` and general FASTA issues to `../input-data-formats/SKILL.md`.
