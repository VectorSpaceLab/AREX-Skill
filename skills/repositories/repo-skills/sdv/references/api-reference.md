# SDV root API reference

Use this reference for top-level routing and package facts. Each sub-skill owns deeper signatures and recipes for its workflow.

## Package identity

- Public package/distribution name: `sdv`
- Import root: `sdv`
- Source package version in this snapshot: `1.38.1.dev0`
- Supported Python from package metadata: `>=3.9,<3.15`
- Public project purpose: generate synthetic data for single-table, multi-table, and sequential tabular data.
- License metadata: BUSL-1.1.

## Public install surfaces

```bash
python -m pip install sdv
python -m pip install "sdv[excel]"      # optional pandas Excel engines for ExcelHandler workflows
conda install -c pytorch -c conda-forge sdv
```

Runtime dependencies from package metadata include `boto3`, `botocore`, `cloudpickle`, `graphviz`, `numpy`, `pandas`, `tqdm`, `copulas`, `ctgan`, `deepecho`, `rdt`, `sdmetrics`, `platformdirs`, and `pyyaml`. Optional extras include `excel` and `pomegranate`; developer/test extras are not needed for ordinary package use.

## Public module map

| Import | Main role | Owning route |
| --- | --- | --- |
| `sdv.datasets.demo` | Public demo datasets, resource text/files, available demo listings. | `data-preparation` |
| `sdv.datasets.local` | Simple `load_csvs` / `save_csvs` folder helpers. | `data-preparation` |
| `sdv.io.local` | `CSVHandler` and `ExcelHandler` local file handlers. | `data-preparation` |
| `sdv.metadata` | Unified `Metadata`, legacy `SingleTableMetadata`, legacy `MultiTableMetadata`, metadata visualization. | `data-preparation` |
| `sdv.constraints` | Legacy tabular constraints and `create_custom_constraint_class`. | `constraints` |
| `sdv.cag` | Current constraint-augmented-generation constraint objects and programmable constraints. | `constraints` |
| `sdv.single_table` | `GaussianCopulaSynthesizer`, `CTGANSynthesizer`, `TVAESynthesizer`, `CopulaGANSynthesizer`, single-table `DayZSynthesizer`. | `single-table` |
| `sdv.lite` | Deprecated `SingleTablePreset`. | `single-table` |
| `sdv.multi_table` | `HMASynthesizer`, multi-table `DayZSynthesizer`. | `multi-table` |
| `sdv.sequential` | `PARSynthesizer`. | `sequential` |
| `sdv.sampling` | `Condition`, `DataFrameCondition`, `MultiTableCondition` and sampler support. | `single-table`, `multi-table`, `sequential` |
| `sdv.evaluation` | Unified `evaluate_quality` and `run_diagnostic`. | `evaluation` |
| `sdv.evaluation.single_table` | Single-table comparison plots. | `evaluation` |
| `sdv.evaluation.multi_table` | Multi-table column and cardinality plots. | `evaluation` |
| `sdv.utils` | `drop_unknown_references`, `get_random_sequence_subset`, `load_synthesizer`, `load_constraints`. | route by function |
| `sdv.logging` / `sdv.logging.utils` | SDV logger access, temporary logger disabling, log CSV loading. | `data-preparation` |

## High-level workflow objects

| Workflow | Primary objects/functions | Next reference |
| --- | --- | --- |
| Data and metadata preparation | `download_demo`, `load_csvs`, `CSVHandler`, `ExcelHandler`, `Metadata.detect_from_dataframe(s)`, `metadata.validate_data`, `metadata.visualize` | [data-preparation API](../sub-skills/data-preparation/references/api-reference.md) |
| Constraint design and attachment | `sdv.cag.FixedCombinations`, `Inequality`, `Range`, `ProgrammableConstraint`, `load_constraints`, `synthesizer.add_constraints` | [constraints API](../sub-skills/constraints/references/api-reference.md) |
| Single-table synthesis | `GaussianCopulaSynthesizer`, `CTGANSynthesizer`, `TVAESynthesizer`, `CopulaGANSynthesizer`, `Condition`, `DataFrameCondition` | [single-table API](../sub-skills/single-table/references/api-reference.md) |
| Relational synthesis | `Metadata.add_relationship`, `HMASynthesizer`, multi-table `DayZSynthesizer`, `drop_unknown_references` | [multi-table API](../sub-skills/multi-table/references/api-reference.md) |
| Sequential synthesis | `Metadata.set_sequence_key`, `Metadata.set_sequence_index`, `PARSynthesizer`, `get_random_sequence_subset` | [sequential API](../sub-skills/sequential/references/api-reference.md) |
| Evaluation | `evaluate_quality`, `run_diagnostic`, `get_column_plot`, `get_column_pair_plot`, `get_cardinality_plot` | [evaluation API](../sub-skills/evaluation/references/api-reference.md) |

## CLI note

This skill is API-first. The source package metadata in this snapshot advertises an `sdv` entry-point group, but the checkout does not include an `sdv.cli` module. Do not tell users to run an SDV CLI unless the target installed distribution separately verifies a real command and help output.

## Environment diagnostic helper

The bundled [check_import.py](../scripts/check_import.py) script verifies imports without depending on the source checkout. Examples from the skill directory:

```bash
python scripts/check_import.py
python scripts/check_import.py --require-dot
python scripts/check_import.py --check-cuda --json
```

Use `--require-dot` when tasks need metadata graph rendering to image/PDF files. Use `--require-cuda` only when the task explicitly requires deep-model GPU execution.
