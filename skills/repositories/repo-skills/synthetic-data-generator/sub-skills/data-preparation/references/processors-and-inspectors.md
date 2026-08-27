# Processors and inspectors

## Metadata inspectors

`Metadata.from_dataframe` and `Metadata.from_dataloader` use `InspectorManager` to infer column types. Relationship inspectors are excluded during single-table metadata inference.

Common inspectors include `DiscreteInspector`, `NumericInspector`, `BoolInspector`, `DatetimeInspector`, `IDInspector`, regex/PII inspectors, `EmptyInspector`, `ConstInspector`, `FixedCombinationInspector`, and `SubsetRelationshipInspector`.

## Default data processors

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

## Processor responsibilities

| Processor | Purpose | Notes |
| --- | --- | --- |
| `SpecificCombinationTransformer` | Enforce user-specified column groups during reverse conversion. | Set `metadata.update({"specific_combinations": {(...columns...)}})`. |
| `FixedCombinationTransformer` | Use automatically detected fixed/correlated combinations. | Stores mappings from first conversion batch; validate on representative data. |
| `NonValueTransformer` | Fill or drop missing values. | Defaults: int `0`, float `0.0`, other `NAN_VALUE`. |
| `OutlierTransformer` | Coerce numeric outliers/unparseable values to fill values. | No-op in reverse conversion. |
| `EmailGenerator` | Remove email columns before model fit and regenerate synthetic emails afterward. | Requires email columns detected in metadata. |
| `ChnPiiGenerator` | Remove/regenerate Chinese-name, ID, phone, and company columns. | Uses Faker `zh_CN`. |
| `IntValueFormatter` | Cast int/id columns back to integer on reverse conversion. | Checks final metadata type before adding columns. |
| `DatetimeFormatter` | Convert datetimes to timestamps and back. | Requires `metadata.datetime_format`; columns without format may be removed. |
| `ConstValueTransformer` | Preserve constant columns. | Restores constant values after sampling. |
| `PositiveNegativeFilter` | Filter sampled rows violating positive/negative numeric constraints. | Constraints come from `metadata.numeric_format`. |
| `EmptyTransformer` | Preserve/drop empty columns. | Works with empty-column metadata. |
| `ColumnOrderTransformer` | Restore original column order and drop extra generated columns. | Keep this last in reverse conversion. |

## Manual processor selection

Pass processors by name, class, or instance through `Synthesizer(..., data_processors=[...])`. When you override the list, keep column-order and formatter behavior if output column fidelity matters.
