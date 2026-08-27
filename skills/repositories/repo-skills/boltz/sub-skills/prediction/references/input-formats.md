# Prediction Input Formats

## Accepted Input Paths

`boltz predict DATA` accepts:

- A single `.yaml` or `.yml` input.
- A single `.fasta`, `.fa`, or `.fas` input.
- A directory whose direct children are only YAML/FASTA input files.

Boltz errors when a directory contains nested directories or files with other suffixes. Keep MSA/template/support files outside the batch input directory.

## YAML Overview

YAML is the preferred format and supports all prediction features:

```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: ACDEFGHIK
      msa: ./msa/a.a3m
  - ligand:
      id: L
      smiles: 'CCO'
constraints:
  - contact:
      token1: [A, 3]
      token2: [L, C1]
      max_distance: 6.0
templates:
  - cif: ./templates/template.cif
    chain_id: A
properties:
  - affinity:
      binder: L
```

Required top-level details:

- `version` defaults to `1`; other versions are rejected.
- `sequences` is required and contains one mapping per unique molecule/entity group.
- Recognized entity keys are `protein`, `dna`, `rna`, and `ligand`.
- Chain IDs must be unique after expanding list IDs.

## Sequences

### Proteins, DNA, and RNA

```yaml
- protein:
    id: [A, B]
    sequence: ACDEFGHIK
    msa: ./msa/a.a3m
    modifications:
      - position: 3
        ccd: MSE
    cyclic: false
```

Rules:

- `id` can be a string or list of strings for identical copies.
- `sequence` is required for `protein`, `dna`, and `rna`.
- `modifications` are optional; positions are 1-based residue indices and use CCD codes.
- `cyclic` is optional and applies to polymers, not ligands.
- Protein `msa` may be omitted for MSA-server generation, set to `empty` for single-sequence mode, or point to `.a3m`/`.csv` files.

### Ligands

```yaml
- ligand:
    id: L
    smiles: 'CCO'
```

```yaml
- ligand:
    id: C
    ccd: SAH
```

Rules:

- Ligands use either `smiles` or `ccd`, not both.
- CCD ligands can be referenced by covalent bond constraints.
- Affinity can target one single-copy ligand chain only.

## MSA Fields

Protein `msa` meanings:

- Omitted, `null`, or empty string: auto MSA placeholder; requires `--use_msa_server` at runtime.
- `empty`: single-sequence mode; runs without MSA but typically reduces accuracy.
- `.a3m`: custom unpaired MSA file for a protein chain/group.
- `.csv`: paired MSA file with columns exactly `sequence` and `key`.

Do not mix custom MSA paths with omitted/auto MSA fields in one YAML target. Boltz rejects mixed custom and auto MSA modes. If using multiple proteins with paired rows, use CSV `key` values to align sequences across chain-specific CSVs.

## A3M Format

An A3M file contains FASTA-like records. Boltz parses headers, uppercase aligned residues, `-` gaps, lowercase insertion characters, and optional `.gz` compression.

Tiny example:

```text
>query
ACDEFGHIK
>hit1
ACDeFG-IK
```

Preflight checks:

- File exists relative to the YAML file or current run directory.
- At least one `>` header and one sequence line exist.
- Characters are plausible protein alignment characters; lowercase insertions are allowed.

## Paired MSA CSV Format

Boltz expects CSV columns exactly `sequence` and `key`:

```csv
sequence,key
ACDEFGHIK,pair1
ACDEYGHIK,pair2
```

The `key` column is used as a pairing/taxonomy identifier. Empty keys are allowed but do not pair rows.

## Constraints

Supported YAML constraint entries:

```yaml
constraints:
  - bond:
      atom1: [A, 145, SG]
      atom2: [L, 1, C1]
  - pocket:
      binder: L
      contacts: [[A, 10], [A, 42]]
      max_distance: 6.0
      force: false
  - contact:
      token1: [A, 10]
      token2: [L, C1]
      max_distance: 6.0
      force: false
```

Rules and warnings:

- Residue indices are 1-based.
- Ligand atom references use atom names; ligand residue index is usually `1` for bond constraints.
- `max_distance` for pocket/contact constraints should be between 4 Å and 20 Å.
- `force: true` uses inference-time potentials. Pair with `--use_potentials` when intentionally steering poses.
- Boltz-1 supports more limited pocket behavior than Boltz-2.

## Templates

Templates are optional and reference local `.cif` or `.pdb` files:

```yaml
templates:
  - cif: ./templates/template.cif
    chain_id: A
  - pdb: ./templates/template.pdb
    chain_id: [A, B]
    template_id: [A1, B1]
  - cif: ./templates/template.cif
    force: true
    threshold: 2.0
```

Rules:

- Provide at least `cif` or `pdb`.
- `chain_id` can be omitted to let Boltz choose best matches.
- Use `template_id` only when explicitly mapping template chains.
- If `force: true`, include `threshold` because the potential needs a tolerated deviation.

## Properties and Affinity

```yaml
properties:
  - affinity:
      binder: L
```

Affinity rules:

- Requires Boltz-2.
- `binder` must match exactly one ligand chain ID.
- The binder ligand cannot have multiple identical copies.
- Only one affinity binder is currently supported.
- Use affinity output for relative small-molecule/protein design contexts, not as a universal physical binding-energy oracle.

## FASTA Format (Deprecated)

FASTA entries use pipe-delimited headers:

```text
>A|protein|./msa/a.a3m
ACDEFGHIK
>B|protein|empty
ACDEFGHIK
>L|smiles
CCO
>C|ccd
SAH
```

Header fields:

- `CHAIN_ID|ENTITY_TYPE|MSA_PATH`
- Entity type is one of `protein`, `dna`, `rna`, `smiles`, or `ccd`.
- The third field is only valid for proteins.

FASTA limitations:

- No modified residues.
- No covalent bonds.
- No pocket/contact conditioning.
- No affinity property.
- YAML should be used for any new complex input.
