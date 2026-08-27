# Cross-cutting troubleshooting

## Import or version failure

- **Symptom:** `Requires-Python` or dependency resolution errors. **Cause:**
  Python is outside 3.12–3.13 or a package pin conflicts. **Recovery:** make a
  fresh isolated environment with a supported Python, install the base package,
  then add only the required `[graph]` or `[nlp]` extra.
- **Symptom:** `import pyhealth` fails inside a checkout. **Cause:** stale
  editable install, mixed package versions, or an optional import. **Recovery:**
  run `python -m pip check`, print `importlib.metadata.version("pyhealth")`,
  and test `import pyhealth` outside the checkout. Do not hide a broken optional
  dependency by editing `sys.path`.

## Optional dependencies

- `torch_geometric` errors belong to the graph route: install `[graph]` only
  for graph models/processors and verify it independently.
- NLP metric/import errors usually mean `[nlp]` is absent. NLTK may additionally
  need a corpus; do not silently download one in a validation script.
- Transformer/model-hub errors can mean missing weights, incompatible versions,
  blocked network, or insufficient memory. First test tokenization/local config;
  acquire weights only with an explicit cache and network decision.

## Data and configuration

- **Missing table/file:** validate the root and expected names before creating a
  dataset; do not guess between MIMIC-III, MIMIC-IV, eICU, OMOP, MEDS, and FHIR
  layouts. See `data-pipelines`.
- **Empty sample dataset:** inspect the task pre-filter, source rows, date
  fields, and processor schema. The package reports that zero transformed
  samples commonly means the task/data contract produced no records.
- **Shape/key error:** compare task output keys with the model's expected
  `input_schema` and `label`/`target` field. See `clinical-tasks` then
  `models-training`; do not patch a collate function first.

## Splitting and evaluation

- Always prefer `split_by_patient` for longitudinal EHR data. `split_by_visit`,
  `split_by_sample`, or random row splits can leak patient information.
- Metric exceptions often indicate wrong mode or shapes: binary metrics expect
  one-dimensional labels/probabilities; multilabel metrics expect aligned
  two-dimensional arrays. Read `evaluation-interpretability` before changing
  thresholds.

## Device/checkpoint failures

- **CUDA unavailable:** inspect `torch.cuda.is_available()` and the PyTorch
  build/driver before changing PyHealth code. Use explicit CPU mode only when
  the experiment's compute claim permits it.
- **Checkpoint load mismatch:** ensure the checkpoint belongs to the same model
  class/config and load it with the same device mapping. Keep checkpoints in a
  known output directory and never overwrite a source dataset.
- **Out of memory:** reduce batch size/sequence length, use a tiny fixture, or
  choose CPU; do not interpret an abbreviated run as a benchmark result.

## Documentation drift

Some older pages and examples use names from PyHealth 1.x (`MIMIC3BaseDataset`,
older split/trainer/evaluator APIs). Confirm names against the current public
exports and focused references before execution.
