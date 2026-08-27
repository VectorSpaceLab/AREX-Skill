# Component map

## High-level flow

SDGX combines tabular data access, metadata inspection, data processing, model fitting, sampling, and evaluation:

```text
DataConnector -> DataLoader -> Metadata/Inspectors -> DataProcessors -> Synthesizer -> Model -> sampled DataFrame -> reverse processors -> optional metrics/export
```

The root package is deliberately plugin-oriented. Managers normalize names with `.strip().lower()` and register classes through pluggy hooks and local module discovery.

## Public managers and current registry facts

| Manager | Public property | Local entries observed | Notes |
| --- | --- | --- | --- |
| `ModelManager` | `registed_models` | `ctgan` | `GaussianCopulaSynthesizerModel` is direct-imported, not registry-listed in the inspected checkout. |
| `DataConnectorManager` | `registed_data_connectors` | `dataframeconnector`, `csvconnector` | `GeneratorConnector` is library-only and not registered by default. |
| `DataProcessorManager` | `registed_data_processors` | default processors plus filter/formatter/transformer/generator classes | Default order is important for fit/sample round trips. |
| `DataExporterManager` | `registed_exporters` | `csvexporter` | CLI `sample` defaults to `CsvExporter`. |
| `CacherManager` | `registed_cachers` | `nocache`, `diskcache` | `DataFrameConnector` defaults to `NoCache`; other connectors default to `DiskCache`. |
| `InspectorManager` | `registed_inspectors` | numeric, discrete, bool, datetime, ID, regex/PII, empty, const, fixed combination, subset relationship | Relationship inspectors are excluded during single-table metadata inference. |

## Default data processor order

`DataProcessorManager().registed_default_processor_list` in the inspected package returns:

1. `specificcombinationtransformer`
2. `fixedcombinationtransformer`
3. `nonvaluetransformer`
4. `outliertransformer`
5. `emailgenerator`
6. `chnpiigenerator`
7. `intvalueformatter`
8. `datetimeformatter`
9. `constvaluetransformer`
10. `positivenegativefilter`
11. `emptytransformer`
12. `columnordertransformer`

The order is part of how `Synthesizer` preserves or restores columns around model training. Do not reorder it casually.

## CLI command set

`sdgx` exposes:

- `fit`: initialize/load a synthesizer, fit or finetune, and save a synthesizer directory.
- `sample`: load a saved synthesizer directory and export sampled data.
- `list-models`, `list-data-connectors`, `list-data-processors`, `list-cachers`, `list-data-exporters`: print registered components.

Common wrapper flags on commands are `--json_output`, `--log_to_file`, and for `fit`/`sample`, `--torchrun` plus `--torchrun_kwargs`.

## Public model families

- ML single table: `CTGANSynthesizerModel` in `sdgx.models.ml.single_table.ctgan`.
- Statistic single table: `GaussianCopulaSynthesizerModel` in `sdgx.models.statistics.single_table.copula`.
- LLM single table: `SingleTableGPTModel` in `sdgx.models.LLM.single_table.gpt`.
- Multi-table data models (`Relationship`, `MetadataCombiner`) exist, but full multi-table synthesizer models are skeletal or roadmap-level in this source state.
