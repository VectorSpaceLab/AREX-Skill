# Troubleshooting

## Missing optional imports

- `from ogb.utils import smiles2graph` fails or the name is absent:
  `rdkit` is missing. Install an rdkit build that matches your Python and
  platform.
- `Pyg*` dataset classes are missing:
  `torch_geometric` and its matching compiled wheels are not installed.
- `Dgl*` dataset classes are missing:
  `dgl` is not installed or the installed build does not match the local torch
  stack.

## Invalid dataset or family name

- `ValueError: Invalid dataset name ...` means the requested dataset string does
  not match the package metadata exactly.
- Use the exact names in [`dataset-catalog.md`](dataset-catalog.md), including
  prefixes like `ogbg-`, `ogbn-`, `ogbl-`, and the exact LSC dataset names.

## Download and cache issues

- The loaders may prompt before downloading large datasets. `Stop download.`
  means the prompt was declined.
- If the loader says a dataset has been updated, the cached version is stale and
  the release file is missing. Remove the old cache or accept the update prompt.
- Large LSC datasets may take substantial time and disk space even before any
  model code runs.

## Split and shape mismatches

- Graph and node evaluators usually expect 2-D arrays shaped like
  `(num_samples, num_tasks)`.
- Link evaluators expect `y_pred_pos` and `y_pred_neg` with the exact ranker
  shapes described by the subskill reference.
- `ogbg-code2` uses list-of-token sequences for `seq_ref` and `seq_pred`.
- `WikiKG90Mv2Evaluator` expects top-10 candidate arrays with the exact
  submission shapes.
- `DatasetSaver` requires the graph, label, and split arrays to line up with the
  packaged graph counts.

## Torch load compatibility

- If `get_idx_split()` or a custom smoke fails when reading a freshly written
  `split_dict.pt`, you may be hitting a newer `torch.load` default that rejects
  non-weights objects by default.
- For trusted local files, load them with `torch.load(path, weights_only=False)`
  or use a torch release that is compatible with the repo's save/load path.
- Keep this in mind when validating tiny export smoke tests that round-trip
  through `DatasetSaver`.

## DatasetSaver errors

- `copy_mapping_dir` requires a `README.md` inside the mapping directory.
- `save_graph_list` must run before `save_target_labels`, `save_split`, and
  `copy_mapping_dir`.
- `save_split` requires `train`, `valid`, and `test` keys.
- Heterogeneous `ogbg` export is not implemented.
- `ogbn` and `ogbl` export do not support multiple graphs.

## Heterogeneous graph caveats

- `ogbn-mag` and related hetero loaders return dict-valued labels and splits.
- The hetero graph readers preserve node and edge types, so key names must match
  the metadata files.
- `__getitem__` for the node/link families usually returns only one graph, so
  indexing and batching differ from the graph-property family.

## LSC-specific caveats

- `PCQM4M` and `WikiKG90M` are deprecated; prefer the `v2` variants.
- `PCQM4Mv2` submission helpers distinguish `test-dev` and `test-challenge`.
- `MAG240M` can require very large RAM for preprocessing or full model runs.
- WikiKG example workflows may depend on external frameworks or checkpoints that
  are not bundled with this repo skill.

## When to use the bundled helpers

- Use `scripts/check-install.py` first when a package or backend import fails.
- Use `scripts/smiles2graph-smoke.py` to confirm the rdkit-backed molecule
  helper works.
- Use `scripts/datasetsaver-tiny-smoke.py` to confirm the dataset-export API
  still works on a toy fixture.
