# Aim SDK API reference

This reference covers the Python SDK surface needed for local Aim tracking and querying. It is self-contained and reflects the verified Aim 3.29.x behavior used for this skill.

## Public imports

Most user code can import from `aim`:

```python
from aim import Audio, Distribution, Figure, Image, Repo, Run, Text
```

For lower-level typing or introspection, use:

```python
from aim.sdk.sequence import Sequence
from aim.sdk.sequence_collection import SequenceCollection
from aim.sdk.types import QueryReportMode
```

Do not instantiate `Sequence` or `SequenceCollection` directly for normal workflows. Get them from `Run.metrics()`, `Repo.query_metrics()`, `Repo.query_images()`, and related query methods.

## Repo

Signature:

```python
Repo(path, *, read_only=None, init=False)
Repo.from_path(path, read_only=None, init=False)
Repo.default_repo(init=False)
```

Use `Repo` to own local repository resources and query stored runs/sequences.

Important methods and attributes:

- `Repo.from_path(path, init=True)`: create/open a local Aim repository rooted at `path`.
- `Repo.exists(path)`: true when `path` already contains an Aim repository.
- `Repo.default_repo(init=False)`: search upward from the current directory for an Aim repository; if none is found, use the current directory. For automation, prefer explicit paths.
- `repo.get_run(run_hash)`: return a read-only `Run` for an existing hash, or `None`.
- `repo.query_runs(query='', paginated=False, offset=None, report_mode=QueryReportMode.PROGRESS_BAR)`: return a `SequenceCollection` over matching runs.
- `repo.query_metrics(query='', report_mode=...)`: return metric sequences.
- `repo.query_images(query='', report_mode=...)`, `repo.query_audios(...)`, `repo.query_figure_objects(...)`, `repo.query_distributions(...)`, `repo.query_texts(...)`: return object sequence collections.
- `repo.collect_sequence_info(sequence_types)`: summarize available sequence names and contexts by sequence type.
- `repo.collect_params_info()`: summarize run parameter trees.
- `repo.close()`: release repository resources; call before deleting a temporary repo directory.

Caveats:

- `Repo(..., read_only=True)` and `Repo.from_path(..., read_only=True)` raise `NotImplementedError` in the verified version. For read access, open a normal `Repo` and use `Run(run_hash, repo=repo, read_only=True)` or `repo.get_run(run_hash)`.
- Repository queries depend on Aim's run index. For a freshly written SDK-only run, close the run and use a bounded `RepoIndexManager.get_index_manager(repo).index(run_hash)` update before asserting `query_runs`, `query_metrics`, or `query_images` results.
- `Repo(path, init=True)`/`Repo.from_path(path, init=True)` are useful for SDK automation. For human CLI workflows, route to `cli-and-services` for `aim init`.
- Remote URLs such as `aim://host:port` are recognized by the SDK, but server startup and remote-service configuration belong to `cli-and-services`.

## Run

Signature:

```python
Run(
    run_hash=None,
    *,
    repo=None,
    read_only=False,
    experiment=None,
    force_resume=False,
    system_tracking_interval=10,
    log_system_params=False,
    capture_terminal_logs=True,
)
```

Use `Run` inside training/evaluation code to track one experiment.

Constructor options:

- `run_hash`: omit for a new run; pass an existing hash to resume or read a run.
- `repo`: a `Repo` object, a path string, a path-like object, or `None` for the default repo.
- `read_only=True`: require `run_hash` and prevent writes; useful for inspection.
- `experiment`: set the run's experiment label when opening/creating.
- `force_resume=True`: forcefully lock/resume a stalled run hash.
- `system_tracking_interval`: interval in seconds for CPU/memory/resource metrics; set `None` to disable.
- `log_system_params=True`: store installed packages, selected environment variables, git info, executable, and arguments under `__system_params`.
- `capture_terminal_logs=True`: duplicate terminal logs into the run; set false in tiny smokes if not needed.

Structured run properties:

- `run.name`, `run.description`, `run.experiment`, `run.archived` are get/set properties.
- `run.creation_time`, `run.created_at`, `run.end_time`, `run.finalized_at`, `run.duration`, `run.active` are inspection properties.
- `run.tags`, `run.add_tag(tag)`, `run.remove_tag(tag)` manage tags.

Run parameters:

```python
run['hparams'] = {'lr': 1e-3, 'batch_size': 32}
run['dataset'] = {'name': 'tiny', 'version': 1}
run[...] = {'all_params': {'replace_or_seed': True}}

lr = run['hparams', 'lr']
maybe = run.get(('hparams', 'missing'), default=None)
run.set(('nested', 'path'), 7)
```

Parameter values can include Python primitives and nested dictionaries/lists/tuples. Keep parameters query-friendly by using strings, numbers, booleans, and shallow structured fields for values you intend to filter.

Lifecycle:

- `run.close()` flushes and releases write-run resources. Always call it explicitly in scripts.
- In the verified Aim 3.29.x behavior, some read-only `Run` objects may raise `AttributeError` during `close()` after their no-op cleanup finalizer has already run; catch that defensively in validation cleanup and still close the owning `Repo`.
- `run.report_progress(expect_next_in=..., block=False)` and `run.report_successful_finish(block=True)` update run status/progress reporters when enabled.

## Tracking values

Signature:

```python
run.track(value, name=None, step=None, epoch=None, *, context=None)
```

Tracking rules:

- For a single scalar/object value, `name` is required.
- For a dictionary of `{sequence_name: value}`, `name` must be `None`; each key becomes a sequence name.
- `context` defaults to `{}` and is part of the sequence identity. The same `name` can safely appear under different contexts.
- `step` defaults to the sequence's next count. Pass explicit `step` when integrating with training loops.
- `epoch` is stored with the record; it can be `None` if not applicable.
- A sequence is homogeneous for a fixed `(run, name, context)`: do not switch from metric scalars to lists/media for the same tuple.

Common patterns:

```python
run.track(0.42, name='loss', step=10, epoch=1, context={'subset': 'train'})
run.track({'loss': 0.37, 'accuracy': 0.91}, step=10, epoch=1, context={'subset': 'val'})
```

Numeric compatibility:

- Python `int`/`float`, NumPy scalar types, and single-item NumPy arrays are accepted as metrics.
- Multi-item NumPy arrays are not accepted as scalar metrics; wrap supported media/object types instead.
- Python `int` and `float` values are compatible within one metric sequence.
- Lists/tuples are accepted as object/list sequences, but changing list element type after it is inferred can raise `ValueError`.

## Object tracking types

Use object wrappers when tracking non-scalar values.

### Image

Signature:

```python
Image(image, caption='', format=None, quality=90, optimize=False)
```

Inputs include an image file path, Pillow image, NumPy array, PyTorch tensor, TensorFlow tensor, or matplotlib figure. Use `Image(fig)` for matplotlib if `Figure(fig)` conversion is fragile. Useful properties/methods: `caption`, `format`, `width`, `height`, `size`, `to_pil_image()`, `json()`.

### Text

Signature:

```python
Text(text)
```

`text` must be a string. Use `text_obj.data` to retrieve the stored string.

### Distribution

Signature:

```python
Distribution(samples=None, bin_count=64, *, hist=None, bin_range=None)
Distribution.from_samples(samples, bin_count=64)
Distribution.from_histogram(hist, bin_range)
```

Use for sampled distributions or existing histogram counts. Useful properties/methods: `bin_count`, `range`, `weights`, `ranges`, `to_np_histogram()`, `json()`.

### Audio

Signature:

```python
Audio(data, format='', caption='', rate=None)
```

Supported formats are `mp3`, `wav`, and `flac`. Inputs can be a file path, bytes, `io.BytesIO`, or a NumPy array for WAV. A NumPy WAV input defaults to rate `22500` if no rate is supplied. Useful methods: `get()` returns bytes in a stream; `to_numpy()` works for WAV.

### Figure

Signature:

```python
Figure(obj)
```

Use for Plotly figures or matplotlib figures. Plotly is the underlying representation. Matplotlib conversion may require Plotly and may not preserve all visual details; `Image(fig)` is often a safer static fallback.

## Sequences

A `Sequence` represents ordered tracked values for one `(run, name, context)`.

Useful fields and methods:

- `sequence.name`, `sequence.context`, `sequence.run`.
- `sequence.values`, `sequence.epochs`, `sequence.timestamps` expose array-like data.
- `sequence.data.items_list()` returns steps plus value/epoch/time columns.
- `sequence.data.numpy()` returns NumPy arrays for steps and columns when supported.
- `sequence.first_step()`, `sequence.last_step()`, `len(sequence)`, `bool(sequence)`.
- Metric sequences provide `metric.dataframe(include_name=False, include_context=False, include_run=False, only_last=False)`.

Run helpers:

- `run.metrics()` returns all metric sequences for one run.
- `run.get_metric(name, context)`, `run.get_image_sequence(name, context)`, `run.get_audio_sequence(...)`, `run.get_figure_sequence(...)`, `run.get_distribution_sequence(...)`, `run.get_text_sequence(...)` retrieve a sequence by exact name/context. Use `aim.storage.context.Context({...})` for exact getter contexts in this Aim version; plain dictionaries are convenient for `run.track(...)` but can be unhashable for getters.
- `run.collect_sequence_info(sequence_types, skip_last_value=False)` summarizes one run's sequences.
- `run.dataframe(include_props=True, include_params=True)` returns a one-row pandas dataframe of run properties and parameters.

## SequenceCollection

Repository queries return `SequenceCollection` objects.

Use:

```python
from aim.sdk.types import QueryReportMode

metrics = repo.query_metrics("metric.name == 'loss'", report_mode=QueryReportMode.DISABLED)
for metric in metrics:
    steps, (values, epochs, times) = metric.data.items_list()

for run_collection in repo.query_runs("run.experiment == 'demo'", report_mode=QueryReportMode.DISABLED).iter_runs():
    run = run_collection.run
```

Important methods:

- `collection.iter()` or direct iteration yields matching sequences.
- `collection.iter_runs()` yields per-run collections for matching runs.
- `collection.dataframe(only_last=False, include_run=True, include_name=True, include_context=True, include_props=True, include_params=True)` concatenates run or sequence dataframes and returns `None` for empty collections.

## Artifacts and logs

Artifact methods:

```python
run.set_artifacts_uri('file:///absolute/path/to/aim-artifacts')
run.log_artifact('/path/to/file.txt', name='file.txt', block=True)
run.log_artifacts('/path/to/directory', name='bundle', block=True)
artifacts = run.artifacts
```

`set_artifacts_uri()` expects a URI scheme such as `file://` or `s3://`; a path without `://` emits a warning. Artifact upload backends and remote storage policy are outside the local SDK smoke scope.

Logging methods:

```python
run.log_info('started training', phase='train')
run.log_warning('validation dipped')
run.log_error('failed batch')
records = run.get_log_records()
terminal_logs = run.get_terminal_logs()
```

`capture_terminal_logs=True` also records terminal output. Disable it for minimal deterministic validation.
