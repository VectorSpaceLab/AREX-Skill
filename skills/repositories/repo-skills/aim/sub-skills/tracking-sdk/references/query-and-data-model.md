# Query and data model workflows

Aim's SDK data model is built around repositories, runs, contexts, and typed sequences. Queries are restricted Python expressions over `run` plus one sequence variable such as `metric` or `images`.

## Mental model

- **Repo**: a local Aim repository containing many runs.
- **Run**: one tracked experiment, with structured properties, tags, parameters, artifacts, and sequences.
- **Run params**: dictionary-like metadata stored via `run[...]`, `run['hparams']`, or `run.set(...)`.
- **Sequence**: ordered records for one `(run, sequence_name, context)`.
- **Context**: a dictionary attached to a sequence. Context distinguishes otherwise identical names such as `loss` for train and validation.
- **Sequence type**: determined by tracked values. Numeric values become metrics; Aim objects become image/text/audio/distribution/figure sequences.

Example identity split:

```python
run.track(0.5, name="loss", context={"subset": "train"}, step=0)
run.track(0.4, name="loss", context={"subset": "val"}, step=0)
```

This creates two metric sequences named `loss`, one for each context.

## Query variables

Repository query methods bind different sequence variables:

| Method | Query variable | Returned sequence class |
| --- | --- | --- |
| `repo.query_runs(query)` | `run` only | per-run `SequenceCollection` |
| `repo.query_metrics(query)` | `run`, `metric` | metric sequences |
| `repo.query_images(query)` | `run`, `images` | image sequences |
| `repo.query_audios(query)` | `run`, `audios` | audio sequences |
| `repo.query_figure_objects(query)` | `run`, `figures` | figure sequences |
| `repo.query_distributions(query)` | `run`, `distributions` | distribution sequences |
| `repo.query_texts(query)` | `run`, `texts` | text sequences |

The variable name must match the method. For example, use `images.name`, not `metric.name`, inside `query_images()`.

## Query syntax

Queries are restricted Python expressions:

```python
"run.experiment == 'baseline'"
"run.hparams.optimizer.lr < 0.01"
"run['hparams', 'batch_size'] == 32"
"run['hparams']['optimizer'].lr == 0.001"
"metric.name == 'loss' and metric.context.subset == 'val'"
"metric.context['subset'] == 'train'"
"images.name == 'samples' and images.context.subset == 'val'"
```

Use Python operators:

- `and`, `or`, `not`; do not use JavaScript-style `&&` or `||`.
- `==`, `!=`, `<`, `<=`, `>`, `>=`.
- String methods that are safe under restricted Python may work, but avoid complex expressions in production automation.
- Builtins such as `min`, `max`, `sum`, `any`, `all`, `sorted`, `datetime`, and `timedelta` are available; arbitrary imports are not.

Aim adds a default archived filter. Empty queries and queries that do not mention `run.archived` behave like:

```python
run.archived == False
```

To include archived runs, mention `run.archived` explicitly:

```python
repo.query_runs("run.archived == True", report_mode=QueryReportMode.DISABLED)
```

## Freshly written runs and query indexes

Repository queries read Aim's indexed run metadata. In normal interactive use, Aim's UI/server/indexing components keep this index current. In a short SDK-only validation process, close the write run and, if a just-written run is not visible to `query_runs()`, `query_metrics()`, or `query_images()`, perform a bounded manual index update before querying:

```python
from aim.sdk.index_manager import RepoIndexManager

run.close()
RepoIndexManager.get_index_manager(repo).index(run_hash)
```

This is the pattern used by the bundled smoke script so that `query_runs`, `query_metrics`, and `query_images` validate freshly written data without starting UI/server processes.

## Query runs

```python
from aim import Repo
from aim.sdk.types import QueryReportMode

repo = Repo.from_path("./aim-repo")
try:
    runs = repo.query_runs(
        "run.experiment == 'classifier' and run.hparams.optimizer.lr < 0.01",
        report_mode=QueryReportMode.DISABLED,
    )
    for run_collection in runs.iter_runs():
        read_run = run_collection.run
        try:
            print(read_run.hash, read_run.name, read_run['hparams'])
        finally:
            read_run.close()
finally:
    repo.close()
```

`query_runs().iter_runs()` yields per-run collections. The actual `Run` is available as `run_collection.run`.

## Query metrics

```python
metrics = repo.query_metrics(
    "metric.name == 'loss' and metric.context.subset == 'val'",
    report_mode=QueryReportMode.DISABLED,
)

for metric in metrics:
    steps, (values, epochs, timestamps) = metric.data.items_list()
    print(metric.run.hash, metric.name, metric.context.to_dict(), list(zip(steps, values)))
    metric.run.close()
```

Use `metric.context.to_dict()` in Python code. In query strings, use `metric.context.subset` or `metric.context['subset']`.

## Query media/object sequences

Images:

```python
images = repo.query_images(
    "images.name == 'samples' and images.context.subset == 'val'",
    report_mode=QueryReportMode.DISABLED,
)
for image_seq in images:
    print(image_seq.name, image_seq.context.to_dict(), len(image_seq))
    # Values are stored as Aim Image objects; use image.to_pil_image() or image.json() after retrieval.
    image_seq.run.close()
```

Texts, distributions, audio, and figures follow the same collection pattern with their method-specific variables:

```python
texts = repo.query_texts("texts.name == 'notes'", report_mode=QueryReportMode.DISABLED)
dists = repo.query_distributions("distributions.name == 'weights'", report_mode=QueryReportMode.DISABLED)
audios = repo.query_audios("audios.context.subset == 'val'", report_mode=QueryReportMode.DISABLED)
figs = repo.query_figure_objects("figures.name == 'plots'", report_mode=QueryReportMode.DISABLED)
```

## Retrieve exact sequences from one run

When you know the run hash and context, exact retrieval is simpler than a repository query:

```python
from aim.storage.context import Context

val_context = Context({"subset": "val"})
read_run = Run(run_hash=run_hash, repo=repo, read_only=True)
try:
    metric = read_run.get_metric("loss", context=val_context)
    if metric:
        steps, (values, epochs, times) = metric.data.items_list()
    images = read_run.get_image_sequence("samples", context=val_context)
    texts = read_run.get_text_sequence("notes", context=val_context)
finally:
    read_run.close()
```

Exact retrieval requires the context to match the tracked context. In this Aim version, exact getters expect Aim's `Context` object; plain dictionaries are accepted by `run.track(...)` but can be unhashable in exact getter calls.

## Dataframes

Run dataframe:

```python
run_df = read_run.dataframe(include_props=True, include_params=True)
```

Metric dataframe:

```python
metric_df = metric.dataframe(include_name=True, include_context=True, include_run=True, only_last=False)
```

Collection dataframe:

```python
metrics_df = repo.query_metrics(
    "metric.name == 'loss'",
    report_mode=QueryReportMode.DISABLED,
).dataframe(only_last=True, include_run=True, include_name=True, include_context=True)
```

Notes:

- Dataframe helpers require pandas to be importable.
- Empty collections return `None`.
- Nested params/context fields are flattened into columns such as `run.hparams.optimizer.lr` or `metric.context.subset`.
- Lists, tuples, and dicts in dataframe cells may be JSON-encoded strings.

## Inspect repository and run sequence summaries

Repository-wide:

```python
info = repo.collect_sequence_info(("metric", "images", "texts", "distributions"))
params = repo.collect_params_info()
```

Run-wide:

```python
run_info = read_run.collect_sequence_info(("metric", "images", "texts"), skip_last_value=True)
for metric in read_run.metrics():
    print(metric.name, metric.context.to_dict(), metric.last_step())
```

## Query edge cases

### Bad logical operators

This is invalid and should raise a `SyntaxError` when the query is compiled/iterated:

```python
"run.hash == 'abc' && metric.name == 'loss'"
```

Use:

```python
"run.hash == 'abc' and metric.name == 'loss'"
```

### Wrong variable for query method

`repo.query_images("metric.name == 'samples'")` does not bind `metric`. It typically produces no useful matches. Use `images.name` with `query_images()`.

### Archived default filter

If a run is archived, empty queries will not return it unless the query explicitly includes `run.archived`.

### Missing params/context fields

Dot and item access to missing fields is converted to a safe missing value inside query evaluation. A typo may silently filter out all results. If expected results are missing, first query less narrowly and print available params/contexts.

### Progress bars in automation

Default query report mode is a progress bar. Use:

```python
report_mode=QueryReportMode.DISABLED
```

in scripts, tests, and non-interactive agents.

## End-to-end validation query

After tracking train/validation losses, validate only validation metrics:

```python
from aim.sdk.types import QueryReportMode

val_losses = []
metrics = repo.query_metrics(
    "metric.name == 'loss' and metric.context.subset == 'val'",
    report_mode=QueryReportMode.DISABLED,
)
for metric in metrics:
    steps, (values, _epochs, _times) = metric.data.items_list()
    val_losses.extend(zip(steps, values))
    metric.run.close()

assert val_losses, "No validation loss metrics found"
assert all(isinstance(step, int) for step, _ in val_losses)
```
