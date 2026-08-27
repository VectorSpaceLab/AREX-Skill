# Conversion and Feature Guidance

This reference covers structure-to-JSON conversion and the feature-building path that turns one Protenix input job into model-ready features. Use it for planning and validation only; running prediction belongs to `../../cli-and-inference/SKILL.md`.

## Structure to JSON with the CLI

The user-facing conversion command is `protenix json`:

```bash
protenix json --input structure.cif --out_dir ./json-out --altloc first
```

Important parameters:

- `--input`: PDB, CIF, mmCIF file, or a directory of structure files.
- `--out_dir`: directory where generated JSON files are written.
- `--altloc`: alternate-location selection. The installed default behavior is `first`.
- `--assembly_id`: optional biological assembly ID to expand before JSON construction.
- `--include_discont_poly_poly_bonds`: include discontinuous polymer-polymer bonds, mainly for cyclic peptides or related cases.

Conversion planning checklist:

1. Prefer CIF/mmCIF when available because it preserves richer entity, assembly, residue, and ligand metadata than PDB.
2. Choose `assembly_id` deliberately. Without it, conversion may reflect the asymmetric unit instead of the desired biological assembly.
3. Use `--altloc first` for deterministic default conversion unless a specific alternate conformation is biologically required.
4. Enable `--include_discont_poly_poly_bonds` only when discontinuous polymer-polymer bonds are intended, such as cyclic peptide handling.
5. Inspect generated `sequences`, copy counts, `id` fields, ligand grouping, and `covalent_bonds` before prediction.

## Conversion APIs

When a Protenix Python environment is available, the installed conversion function is:

```python
from protenix.data.inference.json_maker import cif_to_input_json

job = cif_to_input_json(
    mmcif_file="structure.cif",
    assembly_id=None,
    altloc="first",
    output_json="structure.json",
    sample_name="structure",
    save_entity_and_asym_id=False,
    include_discont_poly_poly_bonds=False,
)
```

Verified signature:

```text
cif_to_input_json(mmcif_file, assembly_id=None, altloc='first', output_json=None, sample_name=None, save_entity_and_asym_id=False, include_discont_poly_poly_bonds=False)
```

Behavior to expect:

- Returns one job dictionary.
- Writes a top-level `[job]` list when `output_json` is supplied.
- Removes water and hydrogens before creating JSON.
- Converts MSE to MET during conversion.
- Derives `proteinChain`, `dnaSequence`, `rnaSequence`, and ligand entities where the source structure maps cleanly.
- Emits nonstandard polymer residues as `CCD_` modifications when possible.
- Detects ligand-polymer and ligand-ligand covalent bonds; discontinuous polymer-polymer bonds require the explicit flag.

Lower-level conversion API:

```python
from protenix.data.inference.json_maker import atom_array_to_input_json

job = atom_array_to_input_json(
    atom_array=atom_array,
    parser=parser,
    assembly_id=None,
    output_json=None,
    sample_name="sample",
    save_entity_and_asym_id=False,
    include_discont_poly_poly_bonds=False,
)
```

Use `atom_array_to_input_json` only when you already have a compatible Biotite atom array and matching parser state. Otherwise, prefer `protenix json` or `cif_to_input_json`.

## PDB and mmCIF Caveats

- PDB input can work, but CIF/mmCIF is safer for biological assemblies, ligand metadata, insertion/alternate-location details, and long identifiers.
- PDB chain-ID and residue-name limitations can make converted JSON less expressive than mmCIF-derived JSON.
- Converted JSON is a starting point, not a guarantee. Always run the bundled validator and inspect entity order, copy counts, and bonds.

## Ligand Parsing Behavior

Ligand entity values determine the parsing path:

- `CCD_ATP`: parsed from CCD/reference component data.
- `CCD_NAG_BMA_BGC`: parsed as one multi-component CCD ligand.
- `FILE_/data/ligand.sdf`: parsed from a ligand structure file with a required 3D conformer.
- `CC(=O)N`: treated as SMILES and embedded with RDKit.

Relevant installed helper behavior:

- `lig_file_to_atom_info(lig_file_path)` supports `.mol`, `.mol2`, `.sdf`, and `.pdb` ligand files and requires a 3D conformer.
- `smiles_to_atom_info(smiles)` uses RDKit conformer generation, including a retry with random coordinates, and can fail or time out for difficult chemistry.
- SMILES and FILE ligands receive generated atom-name mappings that can be used by covalent bonds or atom-level constraints.

Practical choice order:

1. Use `CCD_` when a known CCD component represents the ligand accurately.
2. Use `FILE_` when curated 3D ligand coordinates are required or SMILES embedding is unstable.
3. Use SMILES for lightweight, simple ligands when RDKit conformer generation is acceptable.

## Feature Conversion Path

The feature API converts one job dictionary into atom arrays, token arrays, and feature dictionaries:

```python
from protenix.data.inference.json_to_feature import SampleDictToFeatures

converter = SampleDictToFeatures(single_sample_dict=job, extract_features_for_tfg=False)
feature_dict, atom_array, token_array = converter.get_feature_dict()
```

Key behavior:

- Entity blocks are converted to atom arrays before feature construction.
- `count` expands entity copies.
- Explicit `id` values become chain identifiers and are rejected if duplicated or mismatched with `count`.
- `covalent_bonds` accepts both current `entity1`/`entity2` style and deprecated `left_*`/`right_*` style.
- Contact and pocket constraints are converted into constraint features when the feature path requests them.
- Ligands, ions, proteins, DNA, and RNA contribute different feature dimensions and token classes.

Use feature conversion as a heavier validation step only after lightweight JSON validation passes. It imports Protenix and optional chemistry/template dependencies, but still does not run model inference.

## Static Validation Without Protenix Imports

Use the bundled standalone validator first:

```bash
python scripts/validate_protenix_input_json.py INPUT.json
python scripts/validate_protenix_input_json.py INPUT.json --check-paths
python scripts/validate_protenix_input_json.py INPUT.json --json
```

The validator checks top-level shape, entity families, `count`/`id` consistency, path-like fields, ligand prefixes, current and deprecated covalent bond field names, contact constraints, and pocket constraints. It deliberately does not import Protenix, RDKit, Biotite, gemmi, torch, or model code.

## Template Path Notes

`templatesPath` can point to template search outputs such as `.a3m` and `.hhr`. It may also point to a JSON template list compatible with Protenix template parsing. When authoring JSON by hand, set `templatesPath` only after confirming the selected template workflow produced the expected format for the prediction path.

## What Conversion Does Not Do

- It does not run model prediction.
- It does not generate missing protein MSAs, templates, or RNA MSAs.
- It does not prove that a selected model variant will use constraints or TFG guidance.
- It does not guarantee that optional chemistry dependencies can parse every SMILES or ligand file.
- It can skip uncommon polymer entity types that do not map cleanly to `proteinChain`, `dnaSequence`, or `rnaSequence`.
