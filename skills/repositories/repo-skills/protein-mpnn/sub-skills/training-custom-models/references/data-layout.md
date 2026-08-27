# Training Data Layout

## Required Root Files

A ProteinMPNN training data root must contain:

- `list.csv`: chain metadata used to build train/validation/test clusters.
- `valid_clusters.txt`: integer cluster IDs reserved for validation.
- `test_clusters.txt`: integer cluster IDs reserved for testing.
- `pdb/`: tensor tree containing per-PDB metadata and per-chain tensors.

The public full dataset is large; the sample dataset is much smaller and appropriate for layout validation or debug smoke tests.

## `list.csv` Columns

The training README documents these columns:

- `CHAINID`: chain label in `PDBID_CHAINID` form.
- `DEPOSITION`: deposition date.
- `RESOLUTION`: structure resolution.
- `HASH`: unique sequence hash.
- `CLUSTER`: sequence cluster generated at 30% sequence identity.
- `SEQUENCE`: reference amino-acid sequence.

`training/utils.py` reads `CHAINID`, `HASH`, and integer `CLUSTER`, filters by `RESOLUTION <= --rescut`, and filters `DEPOSITION` before a fixed date cutoff.

## Tensor File Layout

Each PDB entry is represented by one metadata tensor file and one tensor file per chain:

- `pdb/<middle-two-pdbid-chars>/<PDBID>.pt`: metadata for a PDB entry.
- `pdb/<middle-two-pdbid-chars>/<PDBID>_<CHAINID>.pt`: chain tensor for a chain listed in `list.csv`.

The loader derives the metadata prefix from `CHAINID`: it splits `PDBID_CHAINID`, then uses `pdb/<pdbid[1:3]>/<pdbid>`. Keep PDB IDs and chain IDs exactly consistent with `list.csv`.

## Chain Tensor Fields

A `PDBID_CHAINID.pt` chain tensor should include:

- `seq`: amino-acid sequence string.
- `xyz`: atomic coordinates with shape `[L, 14, 3]`.
- `mask`: boolean atom mask with shape `[L, 14]`.
- `bfac`: temperature factors with shape `[L, 14]`.
- `occ`: occupancy with shape `[L, 14]`.

## Metadata Tensor Fields

A `PDBID.pt` metadata tensor should include:

- `method`, `date`, `resolution`, and `chains`.
- `tm`: pairwise similarity values between chains.
- `asmb_ids`, `asmb_details`, `asmb_method`, `asmb_chains`.
- Assembly transforms such as `asmb_xform0`, `asmb_xform1`, etc.; older docs may describe these collectively as `asmb_xformIDX`.

`loader_pdb` uses metadata to select biological assemblies, choose homomeric masked chains, apply transforms, concatenate chains, and return dictionaries consumed by `get_pdbs` and `StructureDataset`.

## Validate Layout Without Loading Huge Tensors

Run the bundled validator from a ProteinMPNN checkout or copy it to any environment with Python:

```bash
python scripts/check_training_layout.py --data-root path/to/pdb_2021aug02 --sample-rows 25
```

The script checks required files, parses cluster IDs, inspects `list.csv`, verifies that sampled metadata and chain `.pt` paths exist, and optionally performs shallow `torch.load` key checks when PyTorch is available. It does not scan the full dataset by default.

Use `--no-torch-load` when running on a machine that should not import PyTorch or touch tensor contents.
