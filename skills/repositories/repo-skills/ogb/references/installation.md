# Installation

## Core install

The repo is a pure Python package. For a local checkout, install it in editable
mode:

```bash
python -m pip install -e .
```

That installs the public `ogb` package and its runtime dependencies. The core
package requires only the standard scientific Python stack and PyTorch.

## Optional helpers and backends

Install the following only when the task needs them:

- `rdkit` for `ogb.utils.smiles2graph` and the molecular workflows in the
  graph-property and LSC subskills.
- `torch_geometric` for `Pyg*` dataset wrappers and the PyG example baselines.
- `dgl` for `Dgl*` dataset wrappers and the DGL example baselines.

The optional backends are not required for the core import/evaluator APIs.
They are only needed when the task explicitly asks for the corresponding
wrapper or example family.

## Verify the install

After installation, run:

```bash
python scripts/check-install.py
```

If you need the molecule helper, also run:

```bash
python scripts/smiles2graph-smoke.py
```

## Common install notes

- Keep the install self-contained; do not rely on the original checkout once
  the generated skill is written.
- If a backend wrapper import fails, check whether the optional backend was
  installed rather than assuming the OGB package is broken.
- The example README files describe additional backend expectations for the
  training baselines, but those baselines are reference workflows, not the core
  runtime package.
- Large LSC examples may need extra data, checkpoints, or external frameworks
  even after the core package is installed.
