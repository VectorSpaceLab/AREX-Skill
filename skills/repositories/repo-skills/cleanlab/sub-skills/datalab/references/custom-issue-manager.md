# Custom IssueManager workflows

## What Datalab expects

A custom issue manager should subclass `cleanlab.datalab.internal.issue_manager.IssueManager` and define:

- `issue_name`
- `find_issues(...)`
- the per-example issue table in `self.issues`
- the dataset-level summary in `self.summary`
- auxiliary metadata in `self.info`

The metaclass builds `issue_score_key` automatically from `issue_name`, so you do **not** set that field yourself.

## Minimum result contract

Your manager should write a `pandas.DataFrame` with at least:

- `is_<issue_name>_issue` — boolean per-example flag
- `<issue_name>_score` — numeric quality score in `[0, 1]`

Then call:

```python
self.summary = self.make_summary(score=float(scores.mean()))
```

If your issue is global rather than example-level, you should still emit a score per example when possible so `report()` and `get_issues()` stay useful.

## Registration

Register the manager before calling `lab.find_issues(...)`:

```python
from cleanlab.datalab.internal.issue_manager_factory import register

register(MyIssueManager, task="classification")
register(MyRegressionIssueManager, task="regression")
register(MyMultilabelIssueManager, task="multilabel")
```

The `@register` decorator is shown in the docs for classification managers. For other tasks, calling `register(...)` explicitly is the clearest option.

If another manager already uses the same `issue_name`, registration overwrites it with a warning.

## Reporting hooks

`Datalab.report()` will call the manager's `report()` implementation automatically.

To make that report useful:

- set a short `description`
- define `verbosity_levels`
- put any reusable report metadata into `self.info`

`verbosity_levels` must map integers to **lists of strings**.
The top verbosity level is one greater than the largest configured level, and prints all remaining info.

## Toy pattern

```python
class ToyIssueManager(IssueManager):
    issue_name = "toy_issue"
    description = "Toy issue used to validate custom registration."
    verbosity_levels = {0: [], 1: ["example_count"]}

    def find_issues(self, **kwargs):
        n = len(self.datalab.data)
        scores = np.linspace(1.0, 0.2, n)
        self.issues = pd.DataFrame(
            {
                "is_toy_issue_issue": scores < 0.5,
                "toy_issue_score": scores,
            }
        )
        self.summary = self.make_summary(score=float(scores.mean()))
        self.info = {"example_count": n}
```

## Common mistakes

- Forgetting `issue_name`.
- Returning scores outside `[0, 1]`.
- Using non-string entries in `verbosity_levels`.
- Registering an issue name that collides with a built-in.
- Failing to populate `self.issues` and `self.summary` before returning.
- Forgetting to check whether the issue should be surfaced by default in `report()`.

## Practical routing

Use a custom manager only when the built-in Datalab issue types are not enough. If the workflow is really standard label cleaning, outlier detection, or structured-label auditing, route to the dedicated sub-skill instead of encoding it as a custom issue manager.
