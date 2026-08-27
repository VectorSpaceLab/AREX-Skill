# Data Preparation Troubleshooting

## Generator says the dataset already exists

**Symptoms**

- The generator prints a message like `Dataset already generated.`
- No new `train/` or `test/` files appear.

**Likely cause**

- The current `config.json` already matches the requested client count,
  partition style, balance flag, and `alpha` value.

**Recovery**

- Run the bundled validator to confirm the tree.
- Only delete or rename the dataset root if you truly want to regenerate it.

## Missing raw data or failed downloads

**Symptoms**

- `wget`, `unzip`, `torchvision.datasets`, or `torchtext.datasets` fails.
- The generator stops before `config.json` is written.

**Likely cause**

- The generator needs network access or an archive that is not present yet.

**Recovery**

- Re-run from a network-enabled environment.
- For Amazon Review and HAR, check the raw archive paths first.
- For AG News and Sogou News, confirm that `torchtext` is installed and can
  fetch the corpora.

## Layout validator fails on `config.json`

**Symptoms**

- The validator cannot find `num_clients` or `num_classes`.
- The recorded client count does not match the file count.

**Likely cause**

- The tree was copied from a different dataset family or partly regenerated.

**Recovery**

- Regenerate the split from the same dataset family.
- Validate again before handing the tree to experiments.

## Client `.npz` files do not round-trip

**Symptoms**

- Loading a split file does not produce a `data` object with `x` and `y`.
- `read_client_data()` later raises a key or shape error.

**Likely cause**

- The output format was modified or the wrong file was copied into the tree.

**Recovery**

- Compare the file against the schema in `references/data-formats.md`.
- Regenerate the dataset instead of patching individual split files.

## Text or sensor preprocessing looks wrong

**Symptoms**

- Token lengths or sensor shapes do not match the model expectations.
- The validator passes, but the later experiment crashes when batching.

**Likely cause**

- The wrong generator was used for the dataset family, or the raw input was not
  preprocessed the way PFLlib expects.

**Recovery**

- Recheck the dataset family and the compatible model family in the experiments
  route.
- Use the exact generator for that dataset family and validate the output tree
  again.
