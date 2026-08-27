# Large-Scale Graph Troubleshooting

## Missing `dig_ext`

- If `dig.lsgraph.dataset` raises `ModuleNotFoundError: No module named 'dig_ext'`, the compiled extension is missing.
- In that case, only the safe import surfaces and `FeatureMomentum` smoke checks are available.

## Sparse Partition / Loader Issues

- `metis` depends on `torch_sparse` partition helpers and sparse adjacency input.
- Confirm the adjacency object is a `SparseTensor` before asking for partitioning.

## FeatureMomentum Pinned-Memory Errors

- `FeatureMomentum` allocates `torch.empty(..., pin_memory=True)` when `device` is `None` or CPU.
- Some CPU-only PyTorch builds report `RuntimeError: Pinned memory requires CUDA` even though no dataset code ran.
- Treat that as a backend allocation limitation; it does not resolve the separate `dig_ext` loader gap.

## OGB or Dataset Download Surprises

- `get_data` can fetch OGB, Reddit, Flickr, Yelp, or SBM data depending on the name.
- Avoid calling it when you only need documentation-level guidance.
