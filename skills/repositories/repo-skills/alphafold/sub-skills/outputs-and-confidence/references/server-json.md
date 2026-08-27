# AlphaFold Server JSON Reference

AlphaFold Server job files are JSON inputs for AlphaFold Server, not for the local `run_alphafold.py` CLI. Use this reference to create or inspect Server job requests without relying on external docs.

## Top-Level Shape

A Server JSON file is always a list of job dictionaries, even for one job:

```json
[
  {
    "name": "Example Job",
    "modelSeeds": [],
    "sequences": [],
    "dialect": "alphafoldserver",
    "version": 1
  }
]
```

Top-level fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | Yes | Human-readable job name shown in Server history. |
| `modelSeeds` | Yes | List of uint32 seed values encoded as strings, or an empty list for automatic seed assignment. Empty list is the recommended default. |
| `sequences` | Yes | List of entity dictionaries to model. |
| `dialect` | Yes | Must be `alphafoldserver`. |
| `version` | Optional/Recommended | For the current documented dialect, use `1`. Version 1 adds `maxTemplateDate` and `useStructureTemplate`. |

JSON comments are not allowed. Use strict JSON syntax, not JSON5, Python dictionaries, or JavaScript object literals.

## Entity Types

Each element of `sequences` is a dictionary with exactly one entity key:

| Entity key | Purpose |
| --- | --- |
| `proteinChain` | Protein sequence plus optional glycans, protein modifications, templates, MSA, and template controls. |
| `dnaSequence` | Single-stranded DNA sequence. Add a second DNA entity for the reverse complement when modeling double-stranded DNA. |
| `rnaSequence` | Single-stranded RNA sequence. |
| `ligand` | Allowed chemical component ligand code. |
| `ion` | Allowed ion code. |

## Protein Chains

Protein chain fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `sequence` | Yes | Protein sequence using the standard 20 amino-acid letters supported by Server. |
| `count` | Yes | Number of copies of this chain. |
| `glycans` | Optional | List of glycan dictionaries with `residues` and 1-based `position`. |
| `modifications` | Optional | List of protein PTM dictionaries. |
| `useStructureTemplate` | Optional | Boolean controlling whether PDB templates are used; defaults to true. |
| `maxTemplateDate` | Optional | `YYYY-MM-DD` upper bound for PDB templates. |
| `unpairedMsa` | Optional | A3M-formatted unpaired MSA string. |
| `templates` | Optional | Custom template mappings with mmCIF text and parallel index arrays. |

Protein modification entries use:

- `ptmType`: allowed CCD modification code.
- `ptmPosition`: 1-based modified residue position.

Documented allowed protein PTM codes are: `CCD_SEP`, `CCD_TPO`, `CCD_PTR`, `CCD_NEP`, `CCD_HIP`, `CCD_ALY`, `CCD_MLY`, `CCD_M3L`, `CCD_MLZ`, `CCD_2MR`, `CCD_AGM`, `CCD_MCS`, `CCD_HYP`, `CCD_HY3`, `CCD_LYZ`, `CCD_AHB`, `CCD_P1L`, `CCD_SNN`, `CCD_SNC`, `CCD_TRF`, `CCD_KCR`, `CCD_CIR`, `CCD_YHA`.

Glycan entries use:

- `residues`: glycan string in the Server-supported glycan notation.
- `position`: 1-based protein residue position.

Template entries use:

- `mmcif`: mmCIF file content as a string.
- `queryIndices`: zero-based query residue indices.
- `templateIndices`: zero-based template residue indices.

`queryIndices` and `templateIndices` are parallel arrays: `queryIndices[i]` maps to `templateIndices[i]`.

## DNA Chains

DNA fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `sequence` | Yes | Single-stranded DNA using `A`, `T`, `G`, and `C`. |
| `count` | Yes | Number of copies. |
| `modifications` | Optional | DNA modification dictionaries. |

DNA modification entries use:

- `modificationType`: allowed CCD modification code.
- `basePosition`: 1-based modified base position.

Documented allowed DNA modification codes are: `CCD_5CM`, `CCD_C34`, `CCD_5HC`, `CCD_6OG`, `CCD_6MA`, `CCD_1CC`, `CCD_8OG`, `CCD_5FC`, `CCD_3DR`.

## RNA Chains

RNA fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `sequence` | Yes | Single-stranded RNA using `A`, `U`, `G`, and `C`. |
| `count` | Yes | Number of copies. |
| `modifications` | Optional | RNA modification dictionaries. |

RNA modification entries use:

- `modificationType`: allowed CCD modification code.
- `basePosition`: 1-based modified base position.

Documented allowed RNA modification codes are: `CCD_PSU`, `CCD_5MC`, `CCD_OMC`, `CCD_4OC`, `CCD_5MU`, `CCD_OMU`, `CCD_UR3`, `CCD_A2M`, `CCD_MA6`, `CCD_6MZ`, `CCD_2MG`, `CCD_OMG`, `CCD_7MG`, `CCD_RSQ`.

## Ligands and Ions

Ligand fields:

- `ligand`: allowed CCD ligand code.
- `count`: number of copies.

Documented allowed ligand codes are: `CCD_ADP`, `CCD_ATP`, `CCD_AMP`, `CCD_GTP`, `CCD_GDP`, `CCD_FAD`, `CCD_NAD`, `CCD_NAP`, `CCD_NDP`, `CCD_HEM`, `CCD_HEC`, `CCD_PLM`, `CCD_OLA`, `CCD_MYR`, `CCD_CIT`, `CCD_CLA`, `CCD_CHL`, `CCD_BCL`, `CCD_BCB`.

Ion fields:

- `ion`: allowed ion code.
- `count`: number of copies.

Documented allowed ion codes are: `MG`, `ZN`, `CL`, `CA`, `NA`, `MN`, `K`, `FE`, `CU`, `CO`.

## Validation Checklist

1. Parse with a strict JSON parser; reject comments and trailing commas.
2. Confirm the root value is a list of job dictionaries.
3. Confirm each job has `dialect: "alphafoldserver"` and, for current jobs, `version: 1`.
4. Confirm `modelSeeds` is a list; prefer an empty list unless the user intentionally sets seed strings.
5. Confirm `sequences` is a non-empty list of single-key entity dictionaries.
6. Confirm sequence alphabets and modification/ligand/ion codes are in the documented allowed sets.
7. Confirm positions are 1-based for modifications/glycans, while template mapping indices are zero-based.
8. Confirm custom template `queryIndices` and `templateIndices` are parallel arrays of equal length.

## Common Dialect Mistakes

- Using a single object at the root instead of a one-element list.
- Adding comments to JSON.
- Setting `dialect` to local AlphaFold, AlphaFold3, or another non-Server value.
- Omitting `count` for an entity.
- Using unsupported modifications or arbitrary CCD codes outside the documented allowlists.
- Using `position` for DNA/RNA base modifications instead of `basePosition`.
- Using 1-based template indices; template mappings are zero-based.
- Confusing AlphaFold Server JSON with local `run_alphafold` FASTA input.
