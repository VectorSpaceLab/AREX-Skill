# QM9 Troubleshooting

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `torch_geometric` import fails or `NNConv` is unavailable | The environment is missing the matching PyG wheels | Install `torch_geometric`, `torch_scatter`, and `torch_sparse` wheels that match the installed torch/CUDA build. |
| The runner cannot load the split artifact | The example was launched from the wrong directory or the bundled split file is missing | Use the bundled `references/random_split.t` path or run from the QM9 workflow root. |
| The dataset root is not writable | PyG caches the dataset under the root you provide | Point the runner at a writable dataset directory. |
| CUDA errors appear during trainer construction | The shared LibMTL trainer is CUDA-first | Use a GPU-backed environment. |
| The model crashes on graph batching | The dataset or loader was not created with the PyG graph API | Use the PyG dataset and loader pattern from the workflow reference. |

## Workflow-specific notes

- The example overrides the scheduler to `reduce` internally.
- The bundled split artifact is part of the benchmark recipe; do not remove it
  when packaging the skill.
