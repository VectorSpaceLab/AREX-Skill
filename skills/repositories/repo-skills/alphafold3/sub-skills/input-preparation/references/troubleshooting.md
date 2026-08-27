# Input Preparation Troubleshooting

Use `scripts/validate_fold_input.py` to reproduce parser errors before running the data pipeline or inference. The script calls `alphafold3.common.folding_input.Input.from_json(json_str, json_path=path)`, so relative path behavior matches normal file-based loading.

## Import and package setup

Symptom: `Unable to import alphafold3.common.folding_input`.

Likely causes:

- AlphaFold 3 is not installed in the active Python environment.
- Generated package data needed by the installed package is missing.

Fixes:

- Activate or select an environment where `import alphafold3` works.
- If package resources are missing after installation, rebuild AlphaFold 3 data resources according to the package installation process.

## Dialect and version errors

Symptom: `AlphaFold 3 input JSON must contain dialect and version fields`.

Likely cause: native JSON is missing required top-level fields.

Fix: add:

```json
"dialect": "alphafold3",
"version": 4
```

Symptom: `unsupported dialect`.

Likely causes:

- Native JSON has a misspelled dialect.
- AlphaFold Server JSON was written as an object instead of a top-level list.

Fixes:

- For native inputs, use `"dialect": "alphafold3"`.
- For AlphaFold Server conversion, wrap fold jobs in a top-level list.

Symptom: `unsupported version`.

Likely cause: version is not one of `1`, `2`, `3`, or `4` for native inputs.

Fix: use `version: 4` for newly authored inputs unless you are preserving an older compatible file.

## Unknown or misplaced keys

Symptom: `Unexpected JSON keys in: ...`.

Likely causes:

- Field is valid in a different entity type but not here.
- A runtime flag was placed inside the input JSON.
- A field name uses AlphaFold Server spelling in native JSON.

Fixes:

- Check the entity-specific allowed fields in `references/input-json.md`.
- Put database, GPU, model, bucket, and inference options in runtime flags; route those questions to `../running-predictions/`.
- Use native field names such as `protein`, `rna`, `dna`, `ligand`, `modelSeeds`, and `bondedAtomPairs`.

## Missing or invalid seeds

Symptom: `must specify at least one rng seed in modelSeeds` or `Input must have at least one RNG seed`.

Likely cause: `modelSeeds` is missing or an empty list in native JSON.

Fix: provide at least one integer-like seed, for example `"modelSeeds": [1]`.

Note: AlphaFold Server JSON can use an empty `modelSeeds` list during conversion, but native AlphaFold 3 JSON cannot.

## Duplicate, unset, or malformed IDs

Symptom: `contains sequences with unset IDs`.

Likely cause: one or more native sequence entities lack an `id`.

Fix: add an ID to every entity.

Symptom: `IDs must be upper case letters`.

Likely causes:

- Lowercase ID such as `a`.
- ID contains digits, underscores, hyphens, or spaces.

Fix: use uppercase alphabetic IDs like `A`, `B`, `AA`, or `LIG`.

Symptom: `contains sequences with duplicate IDs`.

Likely causes:

- Two entities share the same `id`.
- A list-valued `id` creates a copy whose ID is also used elsewhere.

Fix: ensure all expanded IDs are globally unique. Use `id: ["A", "B"]` only for identical copies of one entity.

Symptom: `Chain ... has more than 1 sequence`.

Likely cause: one `sequences` item contains more than one entity type.

Fix: split entries so each item contains exactly one of `protein`, `rna`, `dna`, or `ligand`.

## Mutually exclusive inline/path fields

Symptom: `Only one of unpairedMsa/unpairedMsaPath can be set`.

Fix: choose inline A3M content or a path, not both.

Symptom: `Only one of pairedMsa/pairedMsaPath can be set`.

Fix: choose inline paired A3M content or a path, not both.

Symptom: `Only one of mmcif/mmcifPath can be set`.

Fix: choose inline template mmCIF text or a path, not both.

Symptom: `Only one of userCCD/userCCDPath can be set`.

Fix: choose inline CCD mmCIF text or a path, not both.

Symptom: `Set the ... path using the ...Path field`.

Likely cause: an inline field contains a short string that is also an existing file path.

Fix: move filenames into the matching path field:

- `unpairedMsaPath` instead of `unpairedMsa`.
- `pairedMsaPath` instead of `pairedMsa`.
- `mmcifPath` instead of `mmcif`.
- `userCCDPath` instead of `userCCD`.

## Relative external paths fail

Symptom: `json_path must be specified if path is not absolute`.

Likely cause: relative paths are present but validation called `Input.from_json(json_str)` without the input JSON path.

Fix: validate with a file path-aware parser. The bundled script already does this:

```bash
python sub-skills/input-preparation/scripts/validate_fold_input.py fold_input.json
```

Symptom: file not found for `unpairedMsaPath`, `pairedMsaPath`, `mmcifPath`, or `userCCDPath`.

Likely cause: relative path is not relative to the input JSON file location.

Fix: move the external file next to the JSON or adjust the path relative to the JSON file, not relative to the current shell directory.

## MSA and template issues

Symptom: custom MSA is accepted by JSON parsing but fails later in the data pipeline.

Likely causes:

- A3M first sequence does not exactly match the query sequence.
- Hit rows are not rectangular after lowercase insertions are removed.
- Protein custom MSA sets only one of `unpairedMsa` or `pairedMsa` for a mode that needs both explicitly handled.

Fixes:

- Check A3M formatting and query row.
- For custom unpaired protein MSA, set `pairedMsa` to `""`.
- For fully MSA-free protein, set both `unpairedMsa` and `pairedMsa` to `""`.

Symptom: template mapping fails later or gives confusing alignment results.

Likely causes:

- `queryIndices` and `templateIndices` lengths differ.
- Indices are treated as 1-based instead of 0-based.
- Template mmCIF contains multiple chains or unresolved residues were not counted.

Fixes:

- Use same-length 0-based arrays.
- Use a single-chain protein template mmCIF.
- Include unresolved residues when computing template residue indices.

## Ligands, SMILES, user CCD, and glycans

Symptom: JSON parsing fails with a `JSONDecodeError` around a SMILES string.

Likely cause: backslashes in SMILES were not JSON-escaped.

Fix: double backslashes inside JSON strings. A SMILES containing `C\C=C\C` becomes `"C\\C=C\\C"`.

Symptom: ligand entry is rejected because both `ccdCodes` and `smiles` are set.

Fix: choose one representation. Use CCD codes for standard or custom named components; use SMILES only for unbonded ligands without named atom needs.

Symptom: bond involving a SMILES ligand is rejected.

Likely cause: SMILES ligands do not expose stable atom names.

Fix: define the ligand through `userCCD` or `userCCDPath`, reference its custom code in `ccdCodes`, and define bonds to named atoms.

Symptom: user CCD parsing fails.

Likely causes:

- Missing required CCD mmCIF categories or columns.
- Component ID clashes or contains problematic characters such as `_`.
- `userCCD` contains a filename instead of mmCIF content.

Fixes:

- Provide CCD mmCIF text with component, atom, and bond records.
- Prefer custom names like `LIG-1`, avoiding underscores.
- Use `userCCDPath` when reading from a file.

Symptom: AlphaFold Server glycan input cannot be converted.

Likely cause: server-format glycans are unsupported by the converter.

Fix: rewrite the input in native AlphaFold 3 format as a ligand with multiple CCD components and explicit `bondedAtomPairs`.

## Bonded atom pairs

Symptom: `Bond ... must have 2 atoms`.

Fix: each bond must look like `[["A", 145, "SG"], ["L", 1, "C04"]]`.

Symptom: `Atom ... must have 3 components`.

Fix: each atom must be `[chain_id_string, residue_id_integer, atom_name_string]`.

Symptom: `Invalid chain ID(s) in bond`.

Fix: bond only to expanded IDs that appear in `sequences`.

Symptom: `Invalid residue ID(s) in bond`.

Fix: residue IDs are 1-based and must fit the referenced chain length; for a single-component ligand use residue ID `1`.

Symptom: `Bonds are not unique`.

Fix: remove duplicate bond entries.

## Name sanitisation

Symptom: `Input name must be non-empty and contain at least one valid character`.

Likely cause: `name` is empty or only contains characters stripped from filenames.

Fix: include at least one letter, digit, `_`, `-`, or `.`. Spaces are converted to underscores in output-derived names.

## Runtime flag boundary

Some input-preparation fixes require runtime flags, but the flags do not belong in the JSON:

- RDKit conformer failures may require increasing `--conformer_max_iterations`.
- Custom manually paired MSA may require `--resolve_msa_overlaps=false`.
- AlphaFold Server `maxTemplateDate` must be expressed as the runtime template cutoff flag, not inside server JSON conversion.

Route detailed runtime command construction to `../running-predictions/`.
