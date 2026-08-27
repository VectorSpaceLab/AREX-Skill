# DGL-LifeSci Troubleshooting

Read this for package-wide failures before using a workflow-specific troubleshooting reference.

## Import And Dependency Failures

| Symptom | Likely Cause | What To Do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'dgllife'` | Package not installed in the active Python | Install `dgllife`, or install from a source checkout's `python/` directory for development. Then run `python scripts/check_dgllife_environment.py`. |
| Top-level import prints `RDKit is not installed` | RDKit is missing; many chemistry utilities will fail later | Install RDKit for molecule graph, featurizer, dataset, binding, reaction, and generative workflows. Re-run the nearest validation helper. |
| `ModuleNotFoundError: No module named 'dgl'` | DGL is missing or installed in another Python | Install a DGL wheel compatible with the user's PyTorch/Python platform before constructing graphs. Keep DGL/PyTorch versions consistent. |
| Torch/DGL ABI or backend errors | PyTorch and DGL wheel mismatch, CPU/GPU mismatch, or unsupported Python | Use a clean environment, install PyTorch first, then DGL, then `dgllife`. Prefer CPU for inspection and tiny smoke checks. |
| `sklearn`, `pandas`, `scipy`, `networkx`, `hyperopt`, or `joblib` missing | Base package dependencies were skipped or installed with `--no-deps` | Install missing runtime dependencies before running examples, datasets, hyperparameter search, or metric workflows. |

## Data And Download Boundaries

- Built-in datasets such as MoleculeNet, USPTO, PDBBind, OGB, and pretrained model loaders can trigger downloads or require existing local data. Ask before running them in restricted or expensive environments.
- Cache files such as `*_dglgraph.bin` can silently reuse old featurizers or labels. Delete or rename caches when changing featurizers, task columns, or graph constructors.
- Validate tiny user fixtures first with the nearest bundled script: molecule CSV/TXT, property configs, reaction files, complex file paths, or generative SMILES/vocab files.

## Model And Feature Shape Failures

- Match graph feature fields to model expectations. Many molecule predictors expect `g.ndata['h']`; MPNN/AttentiveFP/Weave-style models also need edge features such as `g.edata['e']`.
- Complete graphs are not the same as molecule bond bigraphs; canonical bond featurizers describe RDKit bonds and do not automatically apply to non-bonded complete-graph edges.
- Inspect constructors with `sub-skills/model-zoo-pretraining/scripts/inspect_model_constructors.py` when a specific `dgllife` version might differ from source docs.

## Workflow Safety

- Treat full training scripts, hyperparameter search, PDBBind/USPTO/OGB workflows, pretrained checkpoint downloads, and molecular generative training as long-running or networked.
- Prefer CPU smoke checks, small fixtures, and import/signature inspection before GPU jobs.
- Keep user outputs, generated configs, caches, and checkpoints in the user's project directory, not inside installed package directories.
