# LSC troubleshooting

## Deprecated datasets

- `PCQM4M` is deprecated; prefer `PCQM4Mv2`.
- `WikiKG90M` is deprecated; prefer `WikiKG90Mv2`.

## Download and memory issues

- LSC datasets are large and may prompt before downloading.
- `MAG240M` can require a very large RAM budget for preprocessing or model
  runs.
- Do not assume the evaluator is broken if the dataset download or checkpoint
  is missing.

## Shape assertions

- Submission helpers enforce exact output shapes.
- `WikiKG90Mv2Evaluator` requires top-10 ranked candidate arrays.
- `PCQM4Mv2Evaluator.save_test_submission()` distinguishes `test-dev` and
  `test-challenge`.

## External framework notes

- Some reference scripts rely on PyG, DGL, DGL-KE, or SMORE.
- Those external stacks are not bundled with the generated OGB runtime skill.
- If a workflow fails only because an external framework is missing, keep the
  core OGB workflow and note the external dependency separately.
