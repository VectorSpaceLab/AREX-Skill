# Clinical-task troubleshooting

- **Unknown task import:** inspect `pyhealth.tasks` exports for the installed
  version. Old `DrugRecDataset`, `MIMIC3BaseDataset`, and evaluator APIs are not
  current proof of a 2.0 class.
- **`set_task` returns no samples:** check source rows, task `pre_filter`, date
  windows, required event types, and patient identifiers. Run the task on one
  synthetic patient before changing worker settings.
- **Missing feature/label key:** compare the task's `input_schema` and
  `output_schema` with the emitted dictionary and the processor/model contract.
  Do not rename labels merely to silence a collator error.
- **Wrong label shape:** binary, multiclass, multilabel, regression, survival,
  and generation tasks have different targets. Route to evaluation before
  choosing a metric or threshold.
- **Data leakage:** samples from one patient in multiple partitions invalidate
  longitudinal estimates. Use patient-level splitting and assert ID sets are
  disjoint.
- **Empty or malformed patient:** return no sample or a clear validation error
  according to task semantics; do not manufacture a clinical label.
- **Credential/network failure:** stop at the access gate. Keep raw clinical
  data and caches outside the skill; use a synthetic/local fixture for API work.
- **Slow transformation:** first reduce to a bounded local cohort and inspect
  task output. Full benchmark transformations may be multiprocessing and
  memory-intensive; they are not import smoke tests.
