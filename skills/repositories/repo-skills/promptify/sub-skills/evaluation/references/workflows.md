# Evaluation Workflows

## Purpose

Read this when you want a quick, copyable evaluation recipe.

## 1. Score a task on an in-memory dataset

```python
from promptify.eval import evaluate
from promptify import Task
from pydantic import BaseModel

class Review(BaseModel):
    sentiment: str

mock_task = Task(model="gpt-4o-mini", output_schema=Review, instruction="Return JSON")
# Replace the engine with a mock in tests or offline docs.
```

The important point is that `evaluate()` expects a callable task-like object and a list of sample dictionaries with `input` and `expected`.

## 2. Use progress reporting

```python
progress_events = []

scores = evaluate(
    task=my_task,
    dataset=my_dataset,
    metrics=["exact_match"],
    progress_callback=lambda current, total: progress_events.append((current, total)),
)
```

The callback receives `(current_index, total_samples)` after each processed row.

## 3. Limit the number of samples

```python
scores = evaluate(
    task=my_task,
    dataset=my_dataset,
    metrics=["exact_match"],
    max_samples=10,
)
```

Use `max_samples` when you only need a quick sanity check or a tiny subset during development.

## 4. Use ROUGE only when the extra is installed

ROUGE depends on `promptify[eval]` because the underlying metric imports rouge-score.

If the environment is missing that extra, skip ROUGE and use exact_match, accuracy, precision, recall, or f1 instead.

## 5. Mock-task pattern for offline evaluation

```python
class MockTask:
    def __init__(self, replies):
        self.replies = replies
        self.index = 0

    def __call__(self, text, **kwargs):
        reply = self.replies[self.index % len(self.replies)]
        self.index += 1
        return reply
```

This is useful when you want to validate the dataset and metric plumbing without contacting a provider.

## 6. Recommended smoke check

Run the bundled helper:

```bash
python scripts/check_promptify.py --mode evaluation
```

That command loads tiny list, JSON, and CSV fixtures, checks the progress callback, and exercises the ROUGE helper when the extra is installed.
