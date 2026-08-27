# Evaluation API Reference

## Purpose

Read this when you need the exact evaluation signatures, the supported metrics, or the way Promptify transforms task outputs into scores.

## Verified signatures

- evaluate(task: Any, dataset: List[Dict[str, Any]], metrics: List[str], max_samples: Optional[int] = None, progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, float]
- load_dataset(source: Union[str, Path, List[Dict[str, Any]]]) -> List[Dict[str, Any]]

## Metric registry

Promptify exposes these metric functions in promptify.eval.metrics:

- precision(predicted, expected) -> float
- recall(predicted, expected) -> float
- f1(predicted, expected) -> float
- accuracy(predicted, expected) -> float
- exact_match(predicted, expected) -> float
- rouge(predicted, expected) -> Dict[str, float]

## Metric behavior

### precision / recall / f1
- Designed for list-like comparisons.
- Dict outputs are flattened into string lists before comparison.
- The final score uses set overlap.

### accuracy
- Compares paired sequences element by element.
- Returns 0.0 if lengths differ or the inputs are empty.

### exact_match
- Compares stringified predicted and expected values after stripping whitespace.

### rouge
- Requires the rouge-score package.
- Returns rouge1, rouge2, and rougeL.
- `evaluate()` consumes rougeL as the scalar score.

## How evaluate works

1. It slices the dataset when `max_samples` is set.
2. It calls the task on each sample input.
3. If the task raises an exception, every metric for that sample gets 0.0 and evaluation continues.
4. It compares each predicted output with the expected value using the selected metrics.
5. It returns rounded mean scores per metric.

## Score-shaping notes

- BaseModel outputs are converted with `model_dump()` before comparison.
- Dict outputs are flattened for precision, recall, and f1.
- A task failure does not abort the run; it only zeros the affected sample.
- Unknown metric names raise EvaluationError.
