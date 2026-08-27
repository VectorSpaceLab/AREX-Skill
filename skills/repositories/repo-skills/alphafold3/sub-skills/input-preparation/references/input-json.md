# AlphaFold 3 Input JSON Reference

AlphaFold 3 accepts either its native `alphafold3` JSON dialect or AlphaFold Server JSON that can be converted. Native inputs are more expressive and should be the default for agent-authored files.

## Native top-level shape

Use one fold job per native JSON file:

```json
{
  "name": "example job",
  "modelSeeds": [1],
  "sequences": [
    {"protein": {"id": "A", "sequence": "PVLSCGEWQL"}},
    {"ligand": {"id": "L", "ccdCodes": ["ATP"]}}
  ],
  "dialect": "alphafold3",
  "version": 4
}
```

Top-level fields:

- `name`: non-empty job name. AlphaFold 3 derives file-safe names by replacing spaces with `_` and keeping only letters, digits, `_`, `-`, and `.`.
- `modelSeeds`: non-empty list of integer-like seeds. Each seed produces a separate model execution.
- `sequences`: non-empty list where each item contains exactly one of `protein`, `rna`, `dna`, or `ligand`.
- `bondedAtomPairs`: optional covalent-bond list, described below.
- `userCCD` / `userCCDPath`: optional custom CCD content or file path. These are mutually exclusive.
- `dialect`: must be `alphafold3` for native JSON.
- `version`: supported native versions are `1`, `2`, `3`, and `4`; current writer output uses `4`.

Version features:

- `1`: initial native input format.
- `2`: external MSA/template path fields: `unpairedMsaPath`, `pairedMsaPath`, and `mmcifPath`.
- `3`: external user CCD path field: `userCCDPath`.
- `4`: optional textual `description` fields on protein, RNA, DNA, and ligand entries.

## Entity IDs and copies

- IDs must be uppercase alphabetic strings such as `A`, `B`, `AA`, or `LIG`.
- Every expanded chain ID must be unique across all proteins, RNAs, DNAs, and ligands.
- `id: ["A", "B"]` means identical copies of the same entity; AlphaFold 3 expands each ID into its own chain.
- Do not use duplicate IDs, lowercase IDs, digits, underscores, or unset IDs.

## Proteins

Minimal protein:

```json
{"protein": {"id": "A", "sequence": "PVLSCGEWQL"}}
```

Common fields:

- `sequence`: amino-acid one-letter sequence. Parser requires letters only.
- `modifications`: list like `{"ptmType": "HY3", "ptmPosition": 1}` with 1-based positions.
- `description`: optional in version 4.
- `unpairedMsa` / `unpairedMsaPath`: inline A3M or path to A3M content; mutually exclusive.
- `pairedMsa` / `pairedMsaPath`: inline A3M or path to A3M content; mutually exclusive.
- `templates`: optional list of structural templates, or `[]` for template-free.

MSA recipes:

- Automatic MSA and template search: omit `unpairedMsa`, `pairedMsa`, and `templates`, or set MSA fields to `null`.
- MSA-free protein: set both `unpairedMsa` and `pairedMsa` to empty strings, and set `templates` to `[]` if template-free.
- Custom unpaired MSA: set `unpairedMsa` or `unpairedMsaPath` and set `pairedMsa` to `""` unless intentionally supplying paired MSA too.
- For manual paired placement across chains, place the crafted alignment in `unpairedMsa`, set `pairedMsa` to `""`, and run prediction with MSA-overlap resolution disabled.

MSA content rules:

- A3M format is FASTA-like and may use lowercase inserted residues and `-` gaps.
- The first MSA sequence must exactly match the query sequence.
- After removing lowercase insertions, all hit rows must match query length.

Template fields:

```json
"templates": [
  {
    "mmcifPath": "templates/chain_a.cif",
    "queryIndices": [0, 1, 2],
    "templateIndices": [5, 6, 7]
  }
]
```

- Use either `mmcif` or `mmcifPath`, not both.
- `queryIndices` and `templateIndices` are 0-based, same-length arrays.
- A template mmCIF should contain one protein chain; account for unresolved residues when choosing `templateIndices`.

## RNA

```json
{"rna": {"id": "R", "sequence": "AGCU", "unpairedMsa": null}}
```

Fields:

- `sequence`: uses `A`, `C`, `G`, and `U`.
- `modifications`: list like `{"modificationType": "2MG", "basePosition": 1}` with 1-based positions.
- `description`: optional in version 4.
- `unpairedMsa` / `unpairedMsaPath`: inline or path A3M; mutually exclusive.

RNA MSA choices:

- Omit or set `unpairedMsa: null` to let the data pipeline build RNA MSA.
- Set `unpairedMsa: ""` for MSA-free RNA.
- Set non-empty A3M content or `unpairedMsaPath` to provide custom RNA MSA.

## DNA

```json
{"dna": {"id": "D", "sequence": "GACCTCT"}}
```

Fields:

- `sequence`: uses `A`, `C`, `G`, and `T`.
- `modifications`: list like `{"modificationType": "6MA", "basePosition": 2}` with 1-based positions.
- `description`: optional in version 4.

DNA entries do not take MSA or template fields.

## Ligands and ions

CCD ligand:

```json
{"ligand": {"id": "L", "ccdCodes": ["ATP"]}}
```

SMILES ligand:

```json
{"ligand": {"id": "S", "smiles": "CC(=O)OC1C[NH+]2CCC1CC2"}}
```

Rules:

- Use `ccdCodes` or `smiles`, not both.
- Ions are ligands; for magnesium use `{"ligand": {"id": "M", "ccdCodes": ["MG"]}}`.
- SMILES ligands cannot participate in `bondedAtomPairs` because SMILES does not provide stable atom names.
- Escape backslashes in SMILES strings for JSON, e.g. `C\\C=C\\C` for a SMILES containing `C\C=C\C`.
- For custom or bonded ligands, prefer user-provided CCD with named atoms, then reference the custom CCD code in `ccdCodes`.

## User-provided CCD

Use `userCCD` for inline CCD mmCIF text, or `userCCDPath` for a file:

```json
{
  "userCCDPath": "ligands/custom_components.cif",
  "sequences": [
    {"ligand": {"id": "L", "ccdCodes": ["LIG-1"]}}
  ]
}
```

Guidance:

- `userCCD` and `userCCDPath` are mutually exclusive.
- `userCCDPath` may be absolute or relative to the input JSON file.
- Plain text, gzip, xz, and zstd-compressed CCD files are readable.
- Avoid underscores in custom component names because they can cause mmCIF issues.
- Include atom IDs, element types, charges, bond definitions, and ideal coordinates when possible; ideal coordinates are used as fallback if conformer generation fails.

## Bonds and glycans

Bond format:

```json
"bondedAtomPairs": [
  [["A", 145, "SG"], ["L", 1, "C04"]],
  [["G", 1, "O6"], ["G", 2, "C1"]]
]
```

Rules enforced by parsing:

- Each bond has exactly two atoms.
- Each atom is `[chain_id, residue_id, atom_name]`.
- `chain_id` must refer to an existing expanded entity ID.
- `residue_id` is 1-based and must fit the referenced chain or ligand component list.
- Duplicate bonds are rejected.
- Bonds involving SMILES ligands are rejected.

Glycans in native input are modeled as ligands with multiple CCD components plus bonds within the glycan and to the protein residue. AlphaFold Server glycan conversion is not supported.

## External file paths

Fields that may read external files:

- Protein: `unpairedMsaPath`, `pairedMsaPath`, template `mmcifPath`.
- RNA: `unpairedMsaPath`.
- Top level: `userCCDPath`.

Path behavior:

- Relative paths are resolved relative to the input JSON file path when `Input.from_json(json_str, json_path=path)` is used.
- If a relative path is used without providing the JSON path to the parser, validation fails because the parser cannot resolve it.
- Do not put a short local filename in inline fields like `unpairedMsa`, `pairedMsa`, `mmcif`, or `userCCD`; if the string looks like an existing file path, the parser tells you to use the corresponding `*Path` field.

## AlphaFold Server conversion

AlphaFold Server JSON is detected when the parsed JSON top level is a list. Each list item is a fold job. A native AlphaFold 3 JSON is a single object.

Supported conversion behavior:

- Fold jobs can omit both `dialect` and `version`, in which case they are treated as AlphaFold Server dialect/version 1.
- If present, AlphaFold Server fold jobs must include both `dialect` and `version`.
- Protein, RNA, DNA, ion, and ligand server sequence types are converted into native chains.
- Server `modelSeeds` are preserved when non-empty; if empty or absent, a random seed is sampled during conversion.
- Server entity copies receive auto-assigned uppercase IDs in reverse spreadsheet order.
- Server ions become native ligands with CCD codes.

Conversion limitations:

- AlphaFold Server JSON without the required top-level list is not detected as server JSON.
- Server glycans are rejected; define glycans in native format with ligands and `bondedAtomPairs`.
- Server `maxTemplateDate` is rejected during conversion; pass template cutoff as a runtime flag instead.

## Parser-backed validation checklist

Before running prediction, confirm:

- Top-level keys are expected; unknown keys are rejected.
- `dialect` is `alphafold3` and `version` is one of `1`, `2`, `3`, `4` for native JSON.
- `modelSeeds` exists and is non-empty.
- `sequences` exists and every sequence has exactly one entity type.
- Every entity has an uppercase alphabetic ID, and expanded IDs are unique.
- Mutually exclusive inline/path pairs are not both set.
- External paths are resolvable from the JSON file path.
- Bond IDs, residue numbers, atom tuple shapes, and uniqueness are valid.
- `userCCD` parses as CCD mmCIF if supplied.

Use the bundled validator for a fast parser check:

```bash
python sub-skills/input-preparation/scripts/validate_fold_input.py fold_input.json
```
