# Experiments Troubleshooting

## CUDA is unavailable

**Symptoms**

- `torch.cuda.is_available()` is `False`
- `main.py` prints `cuda is not available.` and falls back to CPU
- DLG or GPU memory reporting is not meaningful

**Likely cause**

- The runtime does not see a CUDA-capable driver, or `CUDA_VISIBLE_DEVICES`
  hides every GPU.

**Recovery**

- Use the install checker to confirm the backend first.
- Re-run with `-dev cpu` only for a quick smoke if GPU access is not available.
- For benchmark-style runs, restore a CUDA-capable environment and device id.

## FedPAC or other cvxpy-backed runs fail

**Symptoms**

- Import errors from `cvxpy`
- Solver errors inside `FedPAC`
- Quadratic aggregation falls back to local behavior or aborts

**Likely cause**

- `cvxpy` or its solver stack is missing, or the wheel was built against an
  incompatible NumPy version.

**Recovery**

- Keep NumPy below 2 for the torch-compatible stack used in this repo.
- Confirm that `cvxpy` imports in the same environment as `torch`.
- If the solver stack is present but the QP is numerically unstable, inspect
  the algorithm settings and the tiny-round smoke input before assuming the
  dependency stack is broken.

## `main.py` cannot find datasets or results

**Symptoms**

- Relative paths such as `../dataset/` or `../results/` are missing
- A run fails before the server and clients are created

**Likely cause**

- `main.py` was launched from the wrong working directory.

**Recovery**

- Use the bundled experiment launcher, which switches to `system/` for you.
- Make sure the dataset tree exists before the launch.

## Base-head algorithms reject the model

**Symptoms**

- Errors during `FedAvg`, `FedPer`, `FedRep`, `FedPAC`, `FedBABU`, or similar
  setup
- A model lacks the expected `fc` attribute or shape

**Likely cause**

- The selected model does not expose the classifier head that the algorithm
  expects to split or replace.

**Recovery**

- Pick a compatible model family from `references/model-overview.md`.
- If you are extending the repo, ensure the new model follows the same head
  contract or adapt the algorithm registration.

## Text-task runs fail

**Symptoms**

- `torchtext` import or dataset download failures
- Shape errors from `LSTM`, `fastText`, `TextCNN`, or `Transformer`

**Likely cause**

- The text stack is missing, or `-vs` / `-ml` do not match the dataset.

**Recovery**

- Re-check the install stack and the dataset family.
- Use the text model notes in `references/model-overview.md`.
- Confirm that the dataset split tree was generated with the text generator and
  not copied from an image dataset.

## Summaries do not parse

**Symptoms**

- `scripts/summarize_results.py` refuses a file or prints no best accuracies

**Likely cause**

- The file is not an h5 result file or a log that contains `Best accuracy`
  blocks.

**Recovery**

- Point the helper at the h5 file written by `save_results()` or at the text
  log that the run actually produced.
