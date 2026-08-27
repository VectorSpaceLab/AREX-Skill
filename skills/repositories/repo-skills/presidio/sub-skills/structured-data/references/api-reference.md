# API reference

Confirmed against the installed Presidio packages and live API inspection for the structured package surface.

## Import shortcuts

```python
import pandas as pd
from presidio_anonymizer.entities import OperatorConfig
from presidio_structured import (
    StructuredEngine,
    PandasAnalysisBuilder,
    JsonAnalysisBuilder,
    StructuredAnalysis,
    CsvReader,
    JsonReader,
    PandasDataProcessor,
    JsonDataProcessor,
)
```

## Core objects and signatures

- `StructuredEngine(data_processor: Optional[DataProcessorBase] = None) -> None`
- `StructuredEngine.anonymize(data: Union[dict, pandas.DataFrame], structured_analysis: StructuredAnalysis, operators: Optional[Dict[str, OperatorConfig]] = None) -> Union[dict, pandas.DataFrame]`
- `PandasAnalysisBuilder(analyzer: Optional[AnalyzerEngine] = None, analyzer_score_threshold: Optional[float] = None, n_process: int = 1, batch_size: int = 1)`
- `PandasAnalysisBuilder.generate_analysis(df: pandas.DataFrame, n: Optional[int] = None, language: str = "en", selection_strategy: str = "most_common", mixed_strategy_threshold: float = 0.5) -> StructuredAnalysis`
- `JsonAnalysisBuilder(analyzer: Optional[AnalyzerEngine] = None, analyzer_score_threshold: Optional[float] = None, n_process: int = 1, batch_size: int = 1)`
- `JsonAnalysisBuilder.generate_analysis(data: dict, language: str = "en") -> StructuredAnalysis`
- `StructuredAnalysis(entity_mapping: Dict[str, str])`
- `PandasDataProcessor()` and `JsonDataProcessor()` for explicit processor selection.
- `CsvReader.read(path, **kwargs) -> pandas.DataFrame` and `JsonReader.read(path, **kwargs) -> dict` for small file-loading convenience.

## What `StructuredAnalysis` means

`StructuredAnalysis.entity_mapping` maps a DataFrame column name or JSON dot path to an entity type. The entity type is later used to choose an anonymizer operator.

```python
analysis = StructuredAnalysis(
    entity_mapping={
        "Full Name": "PERSON",
        "email": "EMAIL_ADDRESS",
        "address.city": "LOCATION",
    }
)
```

The keys are data keys, not Python attributes. DataFrame columns may include spaces, hyphens, or other non-identifier characters as long as the mapping key exactly matches the column label.

## Engine and processor behavior

- `StructuredEngine()` defaults to `PandasDataProcessor`; pass `StructuredEngine(data_processor=JsonDataProcessor())` for JSON-like data.
- `StructuredEngine.anonymize()` adds a `DEFAULT` replace operator when `operators` is missing or lacks `DEFAULT`.
- Entity-specific operators override `DEFAULT`; otherwise `DEFAULT` handles every mapped entity type.
- `PandasDataProcessor` expects a Pandas `DataFrame`; `JsonDataProcessor` expects a JSON-like `dict` or `list`.
- The processors update the supplied object in place. Pass `df.copy(deep=True)` or `copy.deepcopy(data)` if the original must be preserved.
- The structured package performs anonymization-style operators only. It does not deanonymize structured data directly.

## Analysis builder behavior

- `PandasAnalysisBuilder` analyzes each sampled column value with `BatchAnalyzerEngine.analyze_iterator()` and selects one entity type per column.
- `JsonAnalysisBuilder` analyzes dictionary values with `BatchAnalyzerEngine.analyze_dict()` and produces dotted keys for nested dictionaries.
- Both builders use a Presidio `AnalyzerEngine`. The default analyzer may require the default NLP model; pass a preconfigured analyzer when you need no-download pattern recognizers or custom NLP behavior.
- Use `analyzer_score_threshold` when constructing a builder without a custom analyzer, or pass an `AnalyzerEngine(default_score_threshold=...)` yourself.
- DataFrame sampling uses `df.sample(n, random_state=123)`. If `n` is omitted, all rows are sampled; if `n` exceeds the row count, all rows are used.

## DataFrame selection strategies

`PandasAnalysisBuilder.generate_analysis(..., selection_strategy=...)` supports exactly:

- `most_common`: choose the entity type appearing most often in the sampled column.
- `highest_confidence`: choose the entity type with the strongest analyzer score.
- `mixed`: choose the highest-confidence entity only when its score is above `mixed_strategy_threshold`; otherwise choose `most_common`.

Invalid strategy names raise `ValueError`. For `mixed`, the threshold must be between `0` and `1`.

## CSV and batch APIs related to structured data

For CSV files, either read into a DataFrame and use the structured engine, or use the analyzer/anonymizer batch engines when a dictionary-of-columns workflow is simpler:

```python
from presidio_analyzer import BatchAnalyzerEngine
from presidio_anonymizer import BatchAnonymizerEngine

column_dict = {"email": ["a@example.com", "b@example.com"]}
results = list(BatchAnalyzerEngine(analyzer_engine=my_analyzer).analyze_dict(column_dict, language="en"))
anonymized = BatchAnonymizerEngine().anonymize_dict(results, operators=my_operators)
```

Route analyzer configuration details to `../analyze-text/SKILL.md` and operator details to `../anonymize-text/SKILL.md`.
