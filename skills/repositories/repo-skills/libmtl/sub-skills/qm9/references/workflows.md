# QM9 Workflow

This reference covers the graph-regression benchmark built on QM9 and
`torch_geometric`.

## Workflow launch pattern

Use the QM9 benchmark runner with a CUDA-capable PyG environment and the
bundled split artifact.

## Typical command pattern

```bash
python main.py --weighting EW --arch HPS --dataset_path /path/to/qm9 --gpu_id 0 --mode train --save_path /tmp/libmtl-qm9
```

Important runtime notes:

- The workflow needs `torch_geometric` plus the matching sparse wheels for the
  installed PyTorch build.
- The runner uses the split artifact stored alongside this sub-skill.
- The target list defaults to 11 QM9 regression properties.

## Shared model wiring

- The encoder is graph based.
- `NNConv` provides the message-passing block.
- `Set2Set` pools node features into a molecule-level representation.
- Task-specific linear decoders map the shared representation to each target.

## Workflow checks

1. Confirm the QM9 split artifact exists in this sub-skill's `references/`
   tree.
2. Confirm the dataset root is readable by `torch_geometric.datasets.QM9`.
3. Confirm the sparse PyG wheels match the installed torch / CUDA build.
4. Confirm the runner is launched from the correct working directory or is given
   the correct path to the split artifact.
