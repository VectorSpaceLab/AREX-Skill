# API reference

Confirmed against the installed Presidio packages and live API inspection.

## Import shortcuts

```python
from presidio_anonymizer import (
    AnonymizerEngine,
    DeanonymizeEngine,
    BatchAnonymizerEngine,
    BatchDeanonymizeEngine,
)
from presidio_anonymizer.entities import (
    ConflictResolutionStrategy,
    DictRecognizerResult,
    EngineResult,
    InvalidParamError,
    OperatorConfig,
    OperatorResult,
    RecognizerResult,
)
```

## Core signatures

- `AnonymizerEngine.anonymize(self, text: str, analyzer_results: List[RecognizerResult], operators: Optional[Dict[str, OperatorConfig]] = None, conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.MERGE_SIMILAR_OR_CONTAINED, merge_entities_with_spaces: bool = True) -> EngineResult`
- `DeanonymizeEngine.deanonymize(self, text: str, entities: List[OperatorResult], operators: Dict[str, OperatorConfig]) -> EngineResult`
- `BatchAnonymizerEngine.__init__(self, anonymizer_engine: Optional[AnonymizerEngine] = None)`
- `BatchAnonymizerEngine.anonymize_list(self, texts: List[Optional[Union[str, bool, int, float]]], recognizer_results_list: List[List[RecognizerResult]], **kwargs) -> List[Union[str, Any]]`
- `BatchAnonymizerEngine.anonymize_dict(self, analyzer_results: Iterable[DictRecognizerResult], **kwargs) -> Dict[str, str]`
- `BatchDeanonymizeEngine.__init__(self, deanonymize_engine: Optional[DeanonymizeEngine] = None)`
- `BatchDeanonymizeEngine.deanonymize_list(self, texts: List[Optional[Union[str, bool, int, float]]], entities_list: List[List[OperatorResult]], operators: Dict[str, OperatorConfig]) -> List[Union[str, Any]]`
- `BatchDeanonymizeEngine.deanonymize_dict(self, anonymizer_results: Iterable[DictRecognizerResult], operators: Dict[str, OperatorConfig]) -> Dict[str, Any]`
- `OperatorConfig(operator_name: str, params: Dict = None)`
- `OperatorConfig.from_json(params: Dict) -> OperatorConfig`
- `RecognizerResult(entity_type: str, start: int, end: int, score: float)`
- `OperatorResult(start: int, end: int, entity_type: str, text: str = None, operator: str = None, score: Optional[float] = None)`
- `EngineResult(text: str = None, items: List[OperatorResult] = None)`

## Result objects

- `RecognizerResult` is the input span object. It is what the anonymizer expects after analysis.
- `OperatorResult` is the output span object. It comes back from anonymization or deanonymization.
- `EngineResult.text` is the transformed text.
- `EngineResult.items` is normalized to the final output offsets before return.

## Batch behavior

- `BatchAnonymizerEngine.anonymize_list` forwards extra keyword arguments to `AnonymizerEngine.anonymize`.
- `BatchAnonymizerEngine.anonymize_dict` and `BatchDeanonymizeEngine.deanonymize_dict` recurse through nested dictionaries and lists.
- Scalar values that are not strings, booleans, integers, or floats are preserved as-is.
- `BatchDeanonymizeEngine.deanonymize_list` does not accept passthrough kwargs; unsupported kwargs fail fast.

## Operator plumbing

- `OperatorConfig` pairs an operator name with a parameter dictionary.
- `OperatorConfig.from_json()` consumes a dict with `type` plus operator parameters.
- `InvalidParamError` is the package-level error type for invalid spans, types, operators, and key/parameter validation.
- `AnonymizerEngine` auto-inserts a `DEFAULT` replace operator when the map is empty or missing `DEFAULT`.
- `DeanonymizeEngine` requires an explicit operator map; provide a matching entity key or `DEFAULT` entry.
- `ConflictResolutionStrategy` currently exposes `MERGE_SIMILAR_OR_CONTAINED` and `REMOVE_INTERSECTIONS`.
