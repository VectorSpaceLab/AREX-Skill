# Dataset contribution workflow

## Step order

Follow this exact order when packaging an OGB-compatible dataset:

1. Create the `DatasetSaver` with the dataset name, hetero flag, version, and
   root directory.
2. Save the graph list.
3. Save target labels when the dataset family needs them.
4. Save the split dictionary.
5. Copy the mapping directory.
6. Save task info.
7. Build the metadata dictionary.
8. Zip the release directory.
9. Clean up only after the zip succeeds.

## Family decisions

- `ogbg-*` uses graph-level labels.
- `ogbn-*` uses node-level labels.
- `ogbl-*` does not need `save_target_labels`.
- Heterogeneous graph export is only implemented for the node/link families,
  not for `ogbg` graph-level release packaging.

## Validation strategy

Use a tiny synthetic graph to validate the export path before trying a real
submission. The bundled smoke helper does exactly that and then reloads the
resulting archive through the public graph-property loader.
