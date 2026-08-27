# Advanced Flow Patterns

## Foreach and joins

A foreach split needs an artifact containing a finite iterable:

```python
@step
def start(self):
    self.items = ["a", "bb", "ccc"]
    self.next(self.measure, foreach="items")

@step
def measure(self):
    self.length = len(self.input)
    self.next(self.join)

@step
def join(self, inputs):
    self.lengths = [task.length for task in inputs]
    self.next(self.end)
```

Nested foreach is supported, but keep joins explicit and validate each level's `self.input`, `self.index`, and `self.foreach_stack()` assumptions.

## `merge_artifacts`

`self.merge_artifacts(inputs)` copies non-conflicting artifacts from branches into the join step. It raises when branches produce the same artifact with incompatible values. For branch-specific results, explicitly collect them instead of merging blindly.

## Resume

Use `resume` for a previously started run when you want to reuse successful upstream tasks. Resume can target a step, but code/parameter changes should be deliberate because Metaflow preserves lineage from the origin run.

## Decorator interactions

- `@catch` can provide fallback behavior after failures, but do not combine it with remote patterns that explicitly reject it.
- `@retry` controls user-code retries; total attempts also include fallback attempts.
- `@timeout` values under 60 seconds are invalid for Batch/Kubernetes remote execution.
- `@resources` expresses CPU/GPU/memory/disk needs independently of a concrete backend. Actual backend scheduling is handled by Batch/Kubernetes or another provider.
