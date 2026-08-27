# Dataset recipes and gates

## Synthetic/local recipe

1. Make a tiny list of patient/sample dictionaries.
2. Select processors whose `process` output matches the eventual model input.
3. Fit a `SampleBuilder` on a representative training-only sample set.
4. Validate transformed keys, dtypes, dimensions, and identifiers.
5. Split by patient with a fixed seed and inspect all three lengths/IDs.
6. Build loaders and print one batch without training.

## Real dataset preflight

Before `MIMIC3Dataset`, `MIMIC4*`, `eICUDataset`, `OMOPDataset`, `FHIRDataset`,
`MEDSDataset`, or modality dataset construction, record: source release;
local root; expected files/tables; package config; access/DUA status; network
and cache policy; and a tiny row-count/schema check. A URL or automatic cache
may trigger network I/O. Keep raw data outside generated skill directories.

## Common handoffs

- Dataset has structure but no task samples → read
  [clinical-tasks](../../clinical-tasks/SKILL.md).
- Samples have keys but model rejects them → inspect processor `schema`,
  `dim`, token status, and the model's expected feature/vocabulary contract in
  [models-training](../../models-training/SKILL.md).
- Need image/audio/signal/text field transforms → use this route for generic
  processor mechanics, then [medical-code-text](../../medical-code-text/SKILL.md)
  for modality/model resource gates.
- Need conformal calibration splits → use a four-way split only when the
  evaluation protocol requires train/validation/calibration/test, then route to
  [evaluation-interpretability](../../evaluation-interpretability/SKILL.md).
