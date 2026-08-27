# Graph property troubleshooting

## Missing rdkit

If `smiles2graph` is unavailable, install rdkit for the current Python
platform. The helper is imported lazily through `ogb.utils`.

## Missing PyG or DGL

If the `Pyg*` or `Dgl*` classes are absent, install the matching backend
package. The OGB package itself is still usable through the library-agnostic
loader.

## Wrong metric shape

- `rocauc`, `ap`, `rmse`, and `acc` expect 2-D arrays.
- `ogbg-code2` expects token sequences, not numeric labels.
- If the evaluator complains about task counts, the label array width does not
  match the dataset metadata.

## Download and cache issues

- The loaders may prompt before large downloads.
- A stale cache can trigger the dataset-update prompt if the release marker is
  missing.
- `split_dict.pt` short-circuits split loading when present.

## Code2-specific issues

- `py2graph` style helpers mask the method name deliberately; do not remove the
  masking step when building a reusable helper.
- Syntax errors in the input snippet are expected to fail fast.

## Use the smoke helper

If you only need to confirm the AST path works, run the bundled smoke helper
instead of a full dataset conversion.
