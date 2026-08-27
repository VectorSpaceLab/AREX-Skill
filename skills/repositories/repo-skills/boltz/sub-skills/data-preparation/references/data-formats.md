# Boltz Preprocessed Data Formats And Layouts

This reference describes the artifacts produced by Boltz preprocessing and the paths the training/evaluation data modules expect.

## Minimal Training Data Layout

A single processed dataset should have this logical shape:

```text
processed_targets/
  manifest.json
  records/
    <target_id>.json
  structures/
    <target_id>.npz
processed_msa/
  <msa_id>.npz
symmetry.pkl
```

Training config fields should point to those artifacts:

```yaml
data:
  datasets:
    - _target_: boltz.data.module.training.DatasetConfig
      target_dir: /path/to/processed_targets
      msa_dir: /path/to/processed_msa
      prob: 1.0
  symmetries: /path/to/symmetry.pkl
```

If `manifest_path` is omitted, Boltz loads `target_dir/manifest.json`. If `manifest_path` is supplied, it overrides that default.

## Processed Target Directory

`processed_targets/manifest.json` is loaded by Boltz as a `Manifest`. It can be either:

- A JSON object with a `records` list.
- A bare list of record objects.

Each record describes one target:

- `id`: target identifier used to load `structures/<id>.npz`.
- `structure`: metadata such as resolution, experimental method, release/deposition/revision dates, number of chains, and number of interfaces.
- `chains`: chain metadata including `chain_id`, `chain_name`, `mol_type`, `cluster_id`, `msa_id`, `num_residues`, `valid`, and optionally `entity_id`.
- `interfaces`: chain-pair metadata with validity flags.

`processed_targets/records/<target_id>.json` stores the same per-target record metadata before final aggregation into `manifest.json`.

`processed_targets/structures/<target_id>.npz` contains the arrays used by `boltz.data.types.Structure`:

- `atoms`: atom names, elements, charge, coordinates, conformer coordinates, presence mask, chirality.
- `bonds`: ligand/nonstandard atom bonds.
- `residues`: residue names/types, atom spans, center/disto atom indices, standard/presence flags.
- `chains`: chain names, molecule types, entity/symmetry/asymmetry IDs, atom/residue spans, and cyclic period.
- `connections`: covalent connections across residues/chains.
- `interfaces`: chain pairs with heavy atoms near enough to form interfaces.
- `mask`: valid-chain boolean mask after static filtering.

The training data loader reads structures with:

```text
target_dir / "structures" / f"{record.id}.npz"
```

Then it loads one MSA file for each chain where `chain.msa_id` is not empty and not `-1`.

## Molecule Type IDs

Boltz stores chain molecule types as integer IDs corresponding to:

```text
0 = PROTEIN
1 = DNA
2 = RNA
3 = NONPOLYMER
```

Use this mapping only to interpret processed records and filters. Do not hand-edit processed `.npz` arrays unless reconstructing them through a controlled migration script.

## Processed MSA Directory

`processed_msa/<msa_id>.npz` is loaded as a Boltz `MSA` object with three arrays:

- `sequences`: rows containing `seq_idx`, taxonomy ID, residue slice start/end, deletion slice start/end.
- `residues`: encoded residue tokens for all MSA rows.
- `deletions`: A3M insertion/deletion run metadata with residue index and deletion count.

Raw A3M parsing behavior:

- Empty lines and comment lines are ignored.
- Duplicate sequences are skipped after removing gap characters and uppercasing.
- Lowercase A3M insertion characters are counted as deletions/insertions and do not become aligned residues.
- Headers starting with `>UniRef100` are matched against the taxonomy Redis DB; unmatched or non-UniRef rows get taxonomy `-1`.
- `.a3m.gz` is read with gzip; other suffixes are read as plain text.

Why taxonomy matters:

- Boltz constructs paired MSAs by grouping chains with matching taxonomy IDs.
- Missing taxonomy does not always crash training because dummy/unpaired rows can be created, but multi-chain pairing quality can degrade.

## Raw MSA Name To Processed Name

For the public raw-data pipeline, the raw MSA filename should be the SHA-256 hash of the query sequence:

```python
import hashlib

msa_id = hashlib.sha256(sequence.encode()).hexdigest()
```

Expected raw files:

```text
raw_msa/<msa_id>.a3m
raw_msa/<msa_id>.a3m.gz
```

Expected processed files:

```text
processed_msa/<msa_id>.npz
```

If a target record has `msa_id` set to an empty string, Boltz skips MSA loading for that chain. If it has a hash or other ID, the corresponding `.npz` must exist in `msa_dir`.

## CCD And Symmetry Artifacts

Common CCD-related artifacts:

- `components.cif`: raw wwPDB Chemical Component Dictionary source.
- `ccd.pkl`: pickle mapping CCD codes to RDKit molecules after conformer/symmetry processing.
- `ccd.rdb`: Redis DB used by structure processing to look up CCD molecules from worker processes.
- `symmetry.pkl`: pickle used by training to load ligand symmetry permutations for loss/validation features.

Training reads ligand symmetries through `data.symmetries`. The symmetry loader expects a pickle mapping molecule/CCD keys to RDKit molecules with serialized `symmetries` molecule properties.

Safety note: these pickle files are executable data in Python terms. Only load trusted local artifacts.

## Cluster File

`clustering/clustering.json` maps sequence or ligand identifiers to cluster IDs:

- Protein sequences are keyed by SHA-256 sequence hash after mmseqs clustering.
- Short protein-like sequences and nucleotide sequences map to themselves.
- Ligand CCD codes map to themselves.

Structure processing lowers keys and values when loading clusters, then tries to attach cluster IDs using PDB/entity keys. Missing cluster entries become `-1`.

## Static Structure Filters

RCSB/mmCIF processing applies static filters to mark invalid chains/interfaces:

- Excluded ligands from Boltz constants are masked out.
- Polymer chains with fewer than 4 resolved residues or more than 5000 residues are masked out.
- Protein/DNA/RNA chains made entirely of unknown residues are masked out.
- Protein chains with consecutive CA atoms farther than 10 Å are masked out.
- Chains with substantial inter-chain atom clashes are masked according to a 1.7 Å and 30% clash rule.

These filters affect the `valid` flags in records and the structure `mask`; they are separate from dynamic training filters such as date, resolution, size, subset, or max-residue filters.

## Config Wiring Checklist

Before handing data to training, verify all of these:

- Every `target_dir` exists and contains `manifest.json`, `records/`, and `structures/`.
- Every record ID in `manifest.json` has `structures/<id>.npz`.
- Every non-empty, non-`-1` chain `msa_id` has `msa_dir/<msa_id>.npz`.
- `data.symmetries` points at a trusted readable pickle.
- Dataset split files contain target IDs matching `record.id` values after lowercasing.
- Multiple datasets keep their target/MSA directories paired; do not mix OpenFold targets with PDB MSA paths unless the IDs intentionally match.
- `max_tokens`, `max_atoms`, `max_seqs`, and padding settings are training choices, not preprocessing outputs.
