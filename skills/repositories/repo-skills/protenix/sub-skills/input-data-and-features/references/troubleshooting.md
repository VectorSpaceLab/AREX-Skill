# Input Data Troubleshooting

Use this reference when Protenix rejects input JSON, silently ignores a field, fails during feature construction, or conversion output differs from expectations.

## Invalid Top-Level Shape

Symptoms:

- Validator reports that input JSON must be a non-empty top-level list.
- A single job object is not discovered by downstream commands.

Fix:

```json
[
  {
    "name": "one-job",
    "sequences": [
      {"proteinChain": {"sequence": "ACDE", "count": 1}}
    ]
  }
]
```

- Always wrap jobs in a list, even for one job.
- Each job needs a non-empty string `name` and a non-empty `sequences` list.
- Each sequence item must contain exactly one of `proteinChain`, `dnaSequence`, `rnaSequence`, `ligand`, or `ion`.

## Unknown Entity Family

Symptoms:

- A sequence item uses `protein`, `dna`, `rna`, `smallMolecule`, `entity`, or multiple entity keys.
- Feature construction raises an entity-type error.

Fix:

```json
{
  "sequences": [
    {"proteinChain": {"sequence": "ACDE", "count": 1}},
    {"dnaSequence": {"sequence": "GATTACA", "count": 1}},
    {"rnaSequence": {"sequence": "AUGC", "count": 1}},
    {"ligand": {"ligand": "CCD_ATP", "count": 1}},
    {"ion": {"ion": "MG", "count": 1}}
  ]
}
```

- Use exactly one supported entity key per sequence item.
- Entity numbers in bonds and constraints follow this list order.

## Wrong `count` or `id` Lengths

Symptoms:

- `len(id) != count`.
- Duplicate chain IDs appear inside one entity or across entities.
- Feature construction rejects explicit chain IDs.

Fix:

```json
[
  {
    "name": "explicit-id-demo",
    "sequences": [
      {"proteinChain": {"sequence": "ACDE", "count": 2, "id": ["A", "B"]}},
      {"rnaSequence": {"sequence": "AUGC", "count": 1, "id": ["R"]}}
    ]
  }
]
```

- `id` length must equal `count`.
- Chain IDs must be non-empty strings and unique across the whole job.
- Omit `id` if exact chain IDs are not required.

## Alphabet and Modification Problems

Symptoms:

- Protein sequence contains unsupported letters.
- DNA contains `U`, RNA contains `T`, or either contains punctuation/gaps.
- Modification positions exceed sequence length.
- Modification code lacks `CCD_`.

Fix:

- Protein uses standard amino-acid letters plus `X`.
- DNA uses `A`, `T`, `G`, `C`, and `N`.
- RNA uses `A`, `U`, `G`, `C`, and `N`.
- Protein modifications use `ptmType` and `ptmPosition`.
- DNA/RNA modifications use `modificationType` and `basePosition`.
- Positions are 1-based and should refer to an existing residue/base.

## Deprecated MSA Dictionary

Symptoms:

- JSON contains `msa: {"precomputed_msa_dir": "...", "pairing_db": "uniref100"}`.
- Newer workflows expect explicit `pairedMsaPath` and `unpairedMsaPath`.

Fix:

```json
{
  "proteinChain": {
    "sequence": "ACDEFGHIK",
    "count": 1,
    "pairedMsaPath": "/data/job/msa/pairing.a3m",
    "unpairedMsaPath": "/data/job/msa/non_pairing.a3m"
  }
}
```

- Migrate old `msa.precomputed_msa_dir` values to explicit files when `pairing.a3m` and `non_pairing.a3m` exist.
- Keep the old field only for compatibility with known legacy inputs.
- Route to `../../msa-template-and-prep/SKILL.md` if the files do not exist and must be generated.

## Missing or Relative Paths

Symptoms:

- `pairedMsaPath`, `unpairedMsaPath`, `templatesPath`, or `FILE_` ligand paths work from one directory but fail from another.
- Validator warns about relative paths or fails with `--check-paths`.

Fix:

- Prefer absolute paths for input JSON that will be passed to Protenix commands.
- Use `--check-paths` with the bundled validator before prediction.
- Omit optional path fields when a feature is intentionally disabled instead of leaving misleading placeholders.
- Do not invent MSA/template paths. Generate missing files with the MSA/template workflow.

## Ligand `FILE_`, SMILES, and CCD Confusion

Symptoms:

- Ion is encoded as `CCD_MG` under `ion`.
- Ligand file is treated as SMILES because `FILE_` is missing.
- `FILE_` ligand path points at a 2D file or unsupported suffix.
- SMILES conformer generation times out or fails.

Fix:

```json
[
  {
    "name": "ligand-ion-demo",
    "sequences": [
      {"proteinChain": {"sequence": "ACDEFG", "count": 1, "id": ["A"]}},
      {"ligand": {"ligand": "CCD_ATP", "count": 1, "id": ["L"]}},
      {"ligand": {"ligand": "FILE_/data/ligands/drug.sdf", "count": 1, "id": ["D"]}},
      {"ligand": {"ligand": "CC(=O)N", "count": 1, "id": ["S"]}},
      {"ion": {"ion": "MG", "count": 1, "id": ["M"]}}
    ]
  }
]
```

- Ligands use `CCD_`, `FILE_`, or SMILES.
- Ions use bare CCD codes such as `MG`, `NA`, or `ZN`.
- `FILE_` ligand files should be PDB, SDF, MOL, or MOL2 and contain 3D coordinates.
- Prefer `CCD_` or curated `FILE_` structures when SMILES embedding is unstable.

## Covalent Bond Field Problems

Symptoms:

- Bond works only with legacy `left_*`/`right_*` keys.
- `copy1` is present without `copy2`, or vice versa.
- Copies are omitted but entity copy counts differ.
- No atom is found for the specified entity/position/atom.

Fix:

```json
"covalent_bonds": [
  {
    "entity1": 1,
    "copy1": 1,
    "position1": 12,
    "atom1": "SG",
    "entity2": 2,
    "copy2": 1,
    "position2": 1,
    "atom2": "C1"
  }
]
```

- Prefer current `entity1`, `copy1`, `position1`, `atom1`, `entity2`, `copy2`, `position2`, and `atom2` fields.
- If one copy side is present, both copy sides must be present.
- If both copy sides are omitted, Protenix pairs copies and expects compatible entity counts.
- Use position `1` for single CCD, SMILES, or FILE ligands unless targeting a component of a multi-CCD ligand.
- Polymer-polymer covalent bonds are generally unreliable except cyclic peptide or disulfide-style cases.

## Invalid Constraint References

Symptoms:

- Contact pair reports it is on the same chain.
- `max_distance` is smaller than `min_distance`.
- Pocket binder and pocket residue are the same entity/copy.
- Constraint fields pass JSON validation but have no model effect.

Fix:

```json
"constraint": {
  "contact": [
    {
      "entity1": 1,
      "copy1": 1,
      "position1": 15,
      "entity2": 2,
      "copy2": 1,
      "position2": 4,
      "max_distance": 10
    }
  ],
  "pocket": {
    "binder_chain": {"entity": 3, "copy": 1},
    "contact_residues": [
      {"entity": 1, "copy": 1, "position": 25}
    ],
    "max_distance": 8
  }
}
```

- Use different entity/copy pairs for both sides of contact or pocket constraints.
- Include required `entity`, `copy`, and `position` identifiers.
- Include `max_distance`; set `min_distance` only when needed.
- Constraints are soft and require a prediction configuration that uses constraint features.

## Conversion `altloc` and `assembly_id` Issues

Symptoms:

- Converted JSON has unexpected copy counts or missing chains.
- Ligands are split, merged, or grouped differently than expected.
- Alternate conformations produce surprising coordinates.
- Cyclic peptide bonds are missing.

Fix:

- Prefer CIF/mmCIF input when available.
- Choose `--assembly_id` deliberately when biological assembly expansion matters.
- Use `--altloc first` for deterministic conversion unless a specific alternate should be selected.
- Use `--include_discont_poly_poly_bonds` for cyclic peptide or similar cases that need discontinuous polymer-polymer bonds.
- Inspect converted `sequences` and `covalent_bonds` before prediction.

## RDKit, Biotite, gemmi, and CCD Errors

Symptoms:

- SMILES or ligand-file parsing fails before inference.
- Feature conversion cannot find CCD/reference information.
- mmCIF/PDB parsing fails during conversion.
- Validator passes but Protenix feature conversion fails.

Fix:

- Switch difficult SMILES to curated `FILE_` SDF/MOL2/PDB with 3D coordinates, or to a known `CCD_` component.
- Confirm optional chemistry and structure-parsing dependencies are installed in the Protenix runtime environment.
- Treat CCD/cache refresh as environment maintenance, not as ordinary JSON editing.
- Run the standalone validator first, then a feature-conversion smoke test only in an environment where Protenix and dependencies are installed.
