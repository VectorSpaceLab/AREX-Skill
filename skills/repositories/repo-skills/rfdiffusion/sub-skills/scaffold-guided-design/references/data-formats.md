# Scaffold-Guided Data Formats

RFdiffusion scaffold-guided design uses secondary-structure tensors and block-adjacency tensors as coarse fold conditioning. Runtime skill content must be copied or generated into the user's own project; do not depend on original RFdiffusion checkout examples.

## Scaffold Directory Layout

A scaffold directory contains paired PyTorch tensor files:

```text
scaffolds/tim_barrel/
  barrel01_ss.pt
  barrel01_adj.pt
  barrel02_ss.pt
  barrel02_adj.pt
```

Naming rules:

- Scaffold IDs are the shared basename before `_ss.pt` and `_adj.pt`.
- Every `ID_ss.pt` must have a matching `ID_adj.pt`.
- `scaffoldguided.scaffold_list` entries should be IDs such as `barrel01`, not full tensor filenames.
- If a scaffold list file includes `barrel01_ss.pt`, RFdiffusion normalizes with `item.split(".")[0]` poorly for paired loading; prefer suffix-free IDs.

## Secondary-Structure Tensor

Expected scaffold `*_ss.pt` content:

- Rank: 1D tensor of length `L` for scaffold directory inputs.
- Values: `0=helix`, `1=strand`, `2=loop`, `3=mask/unknown`.
- RFdiffusion one-hot encodes this internally to four classes.

The tensor-generation helper can also create a temporary one-hot form with a PDB residue index column, but the saved scaffold file used by inference is the 1D class tensor.

## Block-Adjacency Tensor

Expected scaffold `*_adj.pt` content:

- Rank: 2D tensor with shape `(L, L)`.
- Values: adjacency/mask classes consumed by RFdiffusion and one-hot encoded internally to three classes.
- Shape must be square and its length must equal the paired secondary-structure tensor length.
- Rows and columns should align to the same residue order as `*_ss.pt`.

The adjacency matrix describes coarse block contacts between secondary-structure elements. Loop and insertion regions are often masked, especially when sampled loop insertions are enabled.

## Target Tensor Layout

For target-bound scaffold-guided binder design, target tensors usually live beside each other:

```text
target_folds/
  target_ss.pt
  target_adj.pt
```

Expected target constraints:

- `target_ss.pt` is a 1D secondary-structure class tensor of target length `T`.
- `target_adj.pt` is a square `(T, T)` block-adjacency tensor.
- If the target PDB is cropped before inference, tensors must correspond to the cropped target, or the same `scaffoldguided.contig_crop` must be applied consistently.
- If `scaffoldguided.target_pdb=True`, `scaffoldguided.target_path` must point to the target PDB used for hotspot numbering and target context.

## Optional Tensor Generation

The RFdiffusion repository includes a helper conceptually equivalent to `make_secstruc_adj.py`: parse one PDB or a directory of PDBs, assign residue secondary structure, build a C-beta distance based block-adjacency matrix, and save `*_ss.pt` plus `*_adj.pt`.

Important dependency notes:

- PyRosetta can provide DSSP-like secondary structure when installed, but it is optional.
- Without PyRosetta, the original helper falls back to an approximate secondary-structure calculation.
- This sub-skill bundles a validation helper, not a full tensor generator, so it does not require PyRosetta.
- If a future agent adapts tensor generation into this skill, keep it self-contained and avoid references to an original checkout path.

## Scaffold Directory Versus Per-Residue Masks

RFdiffusion has two scaffold-guided input styles:

1. `scaffoldguided.scaffold_dir=...` with tensor pairs.
2. No `scaffold_dir`, but at least one per-residue secondary-structure mask such as `contigmap.inpaint_str_helix`, `contigmap.inpaint_str_strand`, or `contigmap.inpaint_str_loop`.

Do not mix these styles. The scaffold-guided model runner asserts that `scaffold_dir` cannot be provided when per-residue secondary-structure masks are also provided.

## Sampled Insertions And Masks

`mask_loops=True` means loop and insertion positions can be masked so the model can choose compatible local structure. This mode supports:

- `scaffoldguided.sampled_insertion=N` or `MIN-MAX` for extra loop residues.
- `scaffoldguided.sampled_N=N` or `MIN-MAX` for N-terminal additions.
- `scaffoldguided.sampled_C=N` or `MIN-MAX` for C-terminal additions.
- `scaffoldguided.ss_mask=N` to mask residues at secondary-structure block boundaries.

`mask_loops=False` means loops are not masked for length expansion. In this mode, RFdiffusion requires:

```text
scaffoldguided.sampled_insertion=0
scaffoldguided.sampled_N=0
scaffoldguided.sampled_C=0
```

## Preflight Checklist

Before running inference:

- Confirm `scaffoldguided.scaffoldguided=True` is present.
- Confirm either `scaffold_dir` or per-residue secondary-structure masks are used, not both.
- Confirm every scaffold has paired `*_ss.pt` and `*_adj.pt` files.
- Confirm each adjacency tensor is square and matches the paired secondary-structure length.
- Confirm target tensors, if supplied, are both present and shape-compatible.
- Confirm hotspots use chain-qualified PDB residue IDs such as `A59`, not zero-based indices.
- Confirm `mask_loops=False` is not combined with any positive sampled insertion, N-addition, or C-addition.
