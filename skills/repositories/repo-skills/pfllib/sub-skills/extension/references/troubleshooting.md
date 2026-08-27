# Extension Troubleshooting

## New algorithm is not selectable

**Symptoms**

- The new algorithm never appears in the CLI choices or registry snapshot.
- The experiment launcher says the algorithm name is unsupported.

**Likely cause**

- The new server/client module was created but never imported into
  `system/main.py`.

**Recovery**

- Add the missing import.
- Add the algorithm branch in the selection block.
- Re-run the registry scanner.

## Model head or shape mismatch

**Symptoms**

- Base-head methods fail when they try to access `model.fc`.
- The classifier output dimension does not match the dataset classes.

**Likely cause**

- The new model does not expose the expected head or was paired with the wrong
  dataset family.

**Recovery**

- Update the model to expose a compatible classifier head.
- Verify the dataset/model pairing in `sub-skills/experiments/references/model-overview.md`.
- If the algorithm needs a head split, wrap the model with the same pattern
  used by the built-in code.

## Dataset generator does not produce a usable tree

**Symptoms**

- `config.json` is missing.
- `train/` or `test/` is incomplete.
- The new dataset works for raw download but fails in `read_client_data()`.

**Likely cause**

- The generator did not call the shared split helpers or the loader path was
  not updated for the new modality.

**Recovery**

- Re-check the generator workflow in `references/workflows.md`.
- Run the layout validator.
- Update the data loader only after the split tree is stable.

## Optional dependency import errors

**Symptoms**

- `cvxpy`, `torchtext`, or `torchvision` import fails only for the new path.

**Likely cause**

- The new feature introduced a dependency that is not present in the current
  environment.

**Recovery**

- Re-run the install checker and add the missing package to the environment.
- Do not assume an existing CPU-only import proves a CUDA or solver path.

## Circular or relative-import issues

**Symptoms**

- The new module imports cleanly in isolation but fails when launched through
  `main.py`.

**Likely cause**

- The new code path depends on a relative import that is not valid from the
  experiment working directory.

**Recovery**

- Keep the new module under the same source root conventions as the existing
  code.
- Re-run the experiment launcher from the bundled wrapper so the working
  directory is normalized.
