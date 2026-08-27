# Data API reference

## Dataset and samples

The public `pyhealth.datasets` exports include `BaseDataset`, many dataset
classes (`MIMIC3Dataset`, `MIMIC4Dataset`, `MIMIC4EHRDataset`, `eICUDataset`,
`OMOPDataset`, `ClinVarDataset`, `FHIRDataset`, `MEDSDataset`, `SampleDataset`),
`SampleBuilder`, `create_sample_dataset`, `split_by_patient`, and
`get_dataloader`. Dataset constructor arguments differ by source; inspect the
class for its documented root/config/table contract rather than guessing.

Verified live signatures in PyHealth 2.0.1:

```text
SampleDataset(path: str, dataset_name: Optional[str] = None,
              task_name: Optional[str] = None, **kwargs)
SampleBuilder(input_schema, output_schema, input_processors=None,
              output_processors=None)
split_by_patient(dataset, ratios, seed=None)
get_dataloader(dataset, batch_size: int, shuffle: bool = False)
```

`SampleBuilder.fit(samples)` requires every sample to contain keys from both
schemas. It builds `patient_to_index` and `record_to_index` mappings, fits
processors, and can save metadata. `SampleDataset` expects a directory with a
`schema.pkl` produced by a fitted builder plus serialized sample chunks. For
small deterministic tests, an in-memory sample dataset is preferable when the
installed package exposes it; for production-scale data use the package's
LitData-backed path.

## Processor contract

A `FeatureProcessor` may implement `fit(samples, field)`, `process(value)`,
`is_token()`, `schema()`, `dim()`, and `spatial()`. The current processor
families include raw, ignore, sequence, nested/deep-nested sequence, text,
label/multihot, tensor, timeseries/temporal-timeseries, tuple-time-text,
image, audio, signal, graph, and StageNet processors. `ModalityType` names
`code`, `text`, `image`, `numeric`, `audio`, and `signal`.

Do not mix raw Python lists, already-batched tensors, and processor outputs
without checking the processor's schema. Route text/vision/audio model choices
to [medical-code-text](../../medical-code-text/SKILL.md).

## Split and loader contract

The splitter requires ratios whose sum is exactly `1.0`; use a seeded split for
reproducibility. `split_by_patient` groups all sample indices belonging to each
patient, while `split_by_visit`/`split_by_sample` can permit longitudinal
leakage. `get_dataloader` accepts a dataset, integer `batch_size`, and optional
`shuffle`; inspect the resulting batch keys before passing it to a model.
