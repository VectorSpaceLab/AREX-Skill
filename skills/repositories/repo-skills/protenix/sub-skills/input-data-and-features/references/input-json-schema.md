# Protenix Input JSON Schema

Protenix inference input is a JSON list. Each item in the list is one modeling job. A minimal job looks like this:

```json
[
  {
    "name": "protein-demo",
    "sequences": [
      {
        "proteinChain": {
          "sequence": "ACDEFGHIKLMNPQRSTVWY",
          "count": 1,
          "id": ["A"]
        }
      }
    ]
  }
]
```

A richer job can combine polymers, ligands, ions, paths, bonds, and constraints:

```json
[
  {
    "name": "protein-rna-ligand-demo",
    "sequences": [
      {
        "proteinChain": {
          "sequence": "ACDEFGHIKLMNPQRSTVWY",
          "count": 1,
          "id": ["A"],
          "pairedMsaPath": "/data/job/pairing.a3m",
          "unpairedMsaPath": "/data/job/non_pairing.a3m",
          "templatesPath": "/data/job/templates.a3m"
        }
      },
      {
        "rnaSequence": {
          "sequence": "AUGGCU",
          "count": 1,
          "id": ["R"],
          "unpairedMsaPath": "/data/job/rna_msa.a3m"
        }
      },
      {
        "ligand": {
          "ligand": "CCD_ATP",
          "count": 1,
          "id": ["L"]
        }
      },
      {
        "ion": {
          "ion": "MG",
          "count": 1,
          "id": ["M"]
        }
      }
    ],
    "covalent_bonds": [
      {
        "entity1": 1,
        "copy1": 1,
        "position1": 5,
        "atom1": "SG",
        "entity2": 3,
        "copy2": 1,
        "position2": 1,
        "atom2": "P"
      }
    ],
    "constraint": {
      "contact": [
        {
          "entity1": 1,
          "copy1": 1,
          "position1": 8,
          "entity2": 2,
          "copy2": 1,
          "position2": 3,
          "max_distance": 12
        }
      ]
    },
    "modelSeeds": [101, 102]
  }
]
```

## Job-Level Fields

- `name`: non-empty string used to identify the job in logs and outputs.
- `sequences`: non-empty list of entity objects. Each entity object contains exactly one supported entity key.
- `covalent_bonds`: optional list of inter-entity bonds. Empty list is valid.
- `constraint`: optional soft structural guidance. Documented keys are `contact` and `pocket`.
- `modelSeeds`: optional list of integer seeds. Prediction must opt into JSON seeds before these affect sampling.
- `assembly_id`: optional metadata emitted by structure conversion when a biological assembly was selected.

Unknown top-level keys are usually ignored by basic JSON handling but should be treated as suspicious unless a specific workflow documents them.

## Entity Blocks

Each item under `sequences` is a one-key dictionary. Valid keys are `proteinChain`, `dnaSequence`, `rnaSequence`, `ligand`, and `ion`.

### Shared Entity Rules

- `count` is required for all entity families and must be a positive integer.
- Optional `id` is a list of non-empty strings whose length equals `count`.
- Explicit chain IDs must be unique inside the entity and across all entities in the same job.
- Omit `id` when chain names are not important; Protenix assigns unused chain IDs automatically.
- Entity numbers used by covalent bonds and constraints are 1-based indexes in the `sequences` list.

### Protein Chains

```json
{
  "proteinChain": {
    "sequence": "MKTFFVLLL",
    "count": 2,
    "id": ["A", "B"],
    "modifications": [
      {"ptmType": "CCD_HY3", "ptmPosition": 1}
    ],
    "pairedMsaPath": "/data/job/pairing.a3m",
    "unpairedMsaPath": "/data/job/non_pairing.a3m",
    "templatesPath": "/data/job/hmmsearch.a3m"
  }
}
```

- `sequence` uses the 20 standard amino-acid letters plus `X` for unknown residues.
- `modifications[].ptmType` uses a `CCD_` code and `ptmPosition` is 1-based.
- `pairedMsaPath` and `unpairedMsaPath` point to existing protein MSA files.
- `templatesPath` points to existing template evidence, commonly `.a3m`, `.hhr`, or a JSON template list accepted by Protenix template parsing.
- Older JSON may contain `msa: {"precomputed_msa_dir": "...", "pairing_db": "uniref100"}`. This remains a compatibility format but new JSON should prefer `pairedMsaPath` and `unpairedMsaPath`.

### DNA and RNA

```json
{
  "dnaSequence": {
    "sequence": "GATTACAN",
    "count": 1,
    "id": ["D"],
    "modifications": [
      {"modificationType": "CCD_6MA", "basePosition": 2}
    ]
  }
}
```

```json
{
  "rnaSequence": {
    "sequence": "AUGCN",
    "count": 1,
    "id": ["R"],
    "unpairedMsaPath": "/data/job/rna_msa.a3m"
  }
}
```

- `dnaSequence` describes one DNA strand. Model double-stranded DNA by adding a second `dnaSequence` entry for the reverse-complement strand.
- DNA sequence letters are `A`, `T`, `G`, `C`, and `N`.
- RNA sequence letters are `A`, `U`, `G`, `C`, and `N`.
- Nucleic acid modifications use `modificationType` with `CCD_` and 1-based `basePosition`.
- RNA `unpairedMsaPath` points to an existing RNA MSA file. Protein-style `pairedMsaPath` and `templatesPath` are not documented RNA fields.

### Ligands

```json
{"ligand": {"ligand": "CCD_ATP", "count": 1, "id": ["L"]}}
```

```json
{"ligand": {"ligand": "FILE_/data/ligands/compound.sdf", "count": 1}}
```

```json
{"ligand": {"ligand": "CC(=O)N", "count": 1}}
```

- `CCD_*`: one or more CCD components. Multi-component ligands can be encoded as one string such as `CCD_NAG_BMA_BGC`.
- `FILE_*`: ligand file path prefixed by `FILE_`. Supported file suffixes are `.pdb`, `.sdf`, `.mol`, and `.mol2`; the file must contain a 3D conformation.
- Any other string is treated as a SMILES ligand. SMILES conformer generation can fail or time out; use `CCD_` or `FILE_` for more stable inputs.
- The old `glycans` field is not supported as a separate family. Represent glycans as CCD ligands plus covalent bonds, or as SMILES/FILE ligands.

### Ions

```json
{"ion": {"ion": "MG", "count": 2, "id": ["M", "N"]}}
```

- Ion codes use the CCD code without the `CCD_` prefix.
- Do not encode ions as `CCD_MG` under `ion`; that prefix belongs to ligands.
- `FILE_` and SMILES forms are ligand-only and are not valid ion encodings.

## MSA and Template Path Fields

- Fill `pairedMsaPath`, `unpairedMsaPath`, and `templatesPath` only when files already exist and are intended for this job.
- Absolute paths are recommended because Protenix resolves relative paths from the process working directory, not from JSON semantics.
- Empty strings are tolerated by some examples as feature-off placeholders, but omitting the field is clearer when the feature is unused.
- If files are missing and need to be generated, route to `../../msa-template-and-prep/SKILL.md` instead of inventing path values.

## Covalent Bonds

Current field names use numbered sides:

```json
{
  "entity1": 1,
  "copy1": 1,
  "position1": 10,
  "atom1": "SG",
  "entity2": 3,
  "copy2": 1,
  "position2": 1,
  "atom2": "C1"
}
```

- `entity1` and `entity2` are 1-based entity indexes from `sequences`.
- `copy1` and `copy2` are optional, but use both together or omit both. If both are omitted, Protenix pairs copies and expects compatible copy counts.
- `position1` and `position2` are 1-based positions. For single CCD, SMILES, or FILE ligands, position is usually `1`; for multi-CCD ligands it indexes the CCD component.
- `atom1` and `atom2` are CCD atom names for polymers and CCD ligands. For SMILES/FILE ligands, atom indexes or generated atom names may be used.
- Deprecated names such as `left_entity`, `left_copy`, `left_position`, `left_atom`, `right_entity`, `right_copy`, `right_position`, and `right_atom` are still recognized by feature code but should be migrated.
- Polymer-ligand and ligand-ligand bonds are the normal use cases. Polymer-polymer bonds are generally unreliable except cyclic peptide and disulfide-style cases.

## Constraint Blocks

`constraint` is optional and describes soft guidance. It is converted during feature construction when the selected workflow uses constraint features.

### Contact Constraint

```json
"constraint": {
  "contact": [
    {
      "entity1": 1,
      "copy1": 1,
      "position1": 72,
      "entity2": 2,
      "copy2": 1,
      "position2": 103,
      "max_distance": 15
    },
    {
      "entity1": 1,
      "copy1": 1,
      "position1": 12,
      "atom1": "CA",
      "entity2": 3,
      "copy2": 1,
      "position2": 1,
      "atom2": "C5",
      "min_distance": 3,
      "max_distance": 6
    }
  ]
}
```

- Required identifiers are `entity*`, `copy*`, and `position*` for both sides.
- `atom1` and `atom2` are optional. When both are present, Protenix treats the pair as atom-contact; otherwise it is token-contact.
- `min_distance` defaults to `0`; `max_distance` must be present and greater than or equal to the minimum.
- Contact constraints cannot target the same entity/copy on both sides.

### Pocket Constraint

```json
"constraint": {
  "pocket": {
    "binder_chain": {"entity": 2, "copy": 1},
    "contact_residues": [
      {"entity": 1, "copy": 1, "position": 69}
    ],
    "max_distance": 8
  }
}
```

- `binder_chain` selects the binder entity/copy.
- `contact_residues` lists target residues.
- Pocket residues cannot be on the same entity/copy as the binder.
- Constraints are soft guidance. JSON validity does not guarantee the chosen prediction configuration applies them.
