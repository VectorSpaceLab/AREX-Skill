# Replay and Streams

This reference explains how DreamerV3's Embodied replay buffer stores per-worker
sequences, how selectors choose sample starts, how chunks are saved/loaded, and
how stream combinators should be used.

## Mental model

Replay receives individual unbatched transitions, usually from a driver callback:

```python
replay = embodied.Replay(length=16, capacity=10000)
driver.on_step(lambda tran, worker: replay.add(tran, worker=worker))
```

For each `worker` id, replay maintains a separate raw-step stream. It inserts a
sampleable item only after that worker has accumulated at least `length`
transitions. Sampling returns sequences that are contiguous within the worker
stream and can span linked chunks from the same worker.

If sampled sequences appear to cross environment streams, the most common cause
is that all transitions were added with the same `worker` id or that data was
mixed later by a stream combinator. Always pass the `worker` argument from the
`Driver` callback into `replay.add()`.

## Replay sequence math

For a single worker:

- Raw steps inserted: `S`.
- Replay `length`: `L`.
- Sampleable sequence starts before capacity: `max(0, S - L + 1)`.
- With `W` workers using stable worker ids, total starts are the sum over
  workers.
- `capacity` limits sampleable starts globally, not raw transitions. For `W`
  workers, choose capacity large enough for the total number of starts you want
  retained across all streams.

Example:

```python
replay = embodied.Replay(length=5, capacity=10)
for step in range(5):
  replay.add({'step': np.int32(step)}, worker=0)
assert len(replay) == 1
batch = replay.sample(batch=1)
assert batch['step'].shape == (1, 5)
assert (batch['step'][0] == np.arange(5)).all()
```

With two workers:

```python
replay = embodied.Replay(length=2, capacity=20)
replay.add({'step': 0, 'worker': 0}, worker=0)
replay.add({'step': 1, 'worker': 1}, worker=1)
replay.add({'step': 2, 'worker': 0}, worker=0)
replay.add({'step': 3, 'worker': 1}, worker=1)
batch = replay.sample(batch=4)
# Each sampled row should be either worker 0's (0, 2) sequence or worker 1's
# (1, 3) sequence; rows should not combine 0 then 3 or 1 then 2.
```

## Transition keys inside replay

When `add(step, worker)` is called:

1. Keys starting with `log/` are dropped. Keep logs in callbacks/logger code if
   they are needed outside replay.
2. Values are converted with `np.asarray`.
3. Replay adds `stepid`, a 20-byte identifier containing the chunk uuid and
   within-chunk index.
4. The raw step is appended to the current chunk for that worker.
5. Once a per-worker stream has at least `length` raw steps, the oldest valid
   start is inserted into the selector.

Therefore training batches usually contain observation keys, policy action
keys, policy-output keys, and `stepid`, but not `log/` keys. They do not
necessarily contain `reset`; use `is_first` and `is_last` for episode-boundary
logic unless your callback explicitly added another boundary key.

## Sampling modes

```python
batch = replay.sample(batch=8, mode='train')
```

- `mode='train'`: increments sample metrics and, when `online=True`, can prefer
  queued online samples.
- `mode='report'` or `mode='eval'`: samples without train sample accounting.
- Sampling waits until the selector is non-empty. If it appears hung, the replay
  probably has fewer than `length` transitions for every worker or transitions
  are not being added.

Returned arrays have shape `(B, T, ...)` where `T == replay.length`. If the key
`is_first` exists, sampled batches are annotated so `is_first[:, 0]` can be
true; `is_last` is also adjusted before a following `is_first` to avoid treating
abandoned episode fragments as continuous.

## Capacity and eviction

`capacity` controls the number of sampleable starts. When full, replay removes
old starts FIFO-style from the item map and selector. Chunks are reference
counted: raw chunks stay in memory/disk while a current stream, sampleable item,
or successor relation still references them. This is why memory can exceed the
minimal size implied by `capacity * length`.

Practical guidance:

- For `W` env workers and replay length `L`, use capacity comfortably above `W`
  if you want all workers represented.
- Capacity that is too small can evict items before priority updates arrive;
  `replay.update()` tolerates stale `stepid`s by ignoring missing chunks.
- A small `chunksize` is useful for tests but creates many chunk files. A large
  `chunksize` reduces files but keeps more raw steps in memory before chunk
  completion.

## Chunks and save/load

Replay chunks are compressed `.npz` files when `directory` is supplied. Chunk
filenames encode timestamp, uuid, successor uuid, and raw length. Do not rename
or edit them manually.

Save behavior:

```python
replay = embodied.Replay(length=16, capacity=1000, directory='replay', save_wait=True)
...
state = replay.save()   # completes non-empty current chunks and writes new chunks
```

- Without `directory`, `save()` does not persist chunks.
- With `directory`, `save()` completes each current non-empty worker chunk,
  submits unsaved chunks to a saver pool, and waits only when `save_wait=True`.
- `save()` returns `None`; the durable state is the chunk directory.

Load behavior:

```python
replay = embodied.Replay(length=16, capacity=1000, directory='replay')
replay.load()
```

- `load(data=None, directory=None, amount=None)` uses the configured directory
  by default.
- It scans `.npz` chunks not already loaded, loads newest chunks first, rebuilds
  references, and inserts valid sequence starts up to `amount` (default capacity
  or unbounded).
- Corrupted chunks can be skipped by the internal chunk loader used during
  replay load; keep logs if expected items are missing.
- Loading does not clear already inserted in-memory data first. If you need a
  clean restore, create a fresh `Replay` instance before `load()`.

## Selectors

Selectors implement `__len__`, `__call__`, `__setitem__`, and `__delitem__`.
Replay stores selector entries as `selector[itemid] = stepids`, where `stepids`
are the sequence `stepid` values for that item.

| Selector | Use when | Behavior |
| --- | --- | --- |
| `selectors.Fifo()` | Need deterministic oldest-start sampling. | Always returns the oldest queued key. Removing non-front keys is supported but slow. |
| `selectors.Uniform(seed=0)` | Default balanced replay sampling. | Samples uniformly over current item ids with a thread lock. |
| `selectors.Recency(uprobs, seed=0)` | Need age-biased sampling. | Samples by age using unnormalized probabilities where earlier entries should be at least as likely as later ones. |
| `selectors.Prioritized(exponent=1.0, initial=1.0, zero_on_sample=False, maxfrac=0.0, branching=16, seed=0)` | Need priority-weighted sequence sampling. | Maintains priorities per step id and aggregates per item through a `SampleTree`. Call `replay.update({'stepid': ..., 'priority': ...})`. |
| `selectors.Mixture(selectors, fractions, seed=0)` | Need a weighted mix of selector policies. | Fractions must cover the same keys as selectors and sum to 1. Priority updates are forwarded to selectors that support them. |

`Prioritized` priority update shape should match `(batch, length)`. Because
items can be evicted, stale updates can be ignored; this is expected under small
capacity or asynchronous learners.

## SampleTree notes

`selectors.SampleTree` backs prioritized selection. It supports:

- `insert(key, uprob)` for unnormalized probability values.
- `remove(key)` and `update(key, uprob)`.
- `sample()` handling positive, zero, and infinite probabilities.

Use it indirectly through `Prioritized` unless building a custom selector. If a
custom selector is needed, mimic the selector protocol rather than changing
Replay internals.

## Streams

Streams are iterator objects with optional state:

```python
stream = iter(stream)
item = next(stream)
state = stream.save()
stream.load(state)
```

### `Stateless`

Wraps a callable or existing iterator:

```python
stream = streams.Stateless(lambda: replay.sample(8))
batch = next(stream)
```

`save()` returns `None`; use it for stateless sampling or synthetic fixtures.

### `Prefetch`

Runs a background thread to prefetch and transform source items:

```python
source = streams.Stateless(lambda: replay.sample(8))
stream = streams.Prefetch(source, transform=lambda x: x, amount=2)
stream = iter(stream)
batch = next(stream)
```

Rules:

- Call `iter(stream)` exactly once before `next()`.
- If the worker raises, `next()` raises `RuntimeError` containing the worker
  error string.
- `load(state)` drains queued items if already started, then delegates to the
  source `load()`.

### `Consec`

Splits larger time batches into consecutive windows:

```python
source = streams.Stateless(lambda: replay.sample(batch=8))  # returns T=64
stream = streams.Consec(source, length=16, consec=4, prefix=0, strict=True)
stream = iter(stream)
for i in range(4):
  chunk = next(stream)
  assert chunk['consec'][0, 0] == i
```

Requirements:

- Source data must have time dimension at `axis=1` for every key.
- Available time must be at least `length * consec + prefix`.
- With `strict=True`, available time must equal exactly that amount.
- `contiguous=True` copies arrays into contiguous memory, which can help
  serialization/networking at extra CPU cost.

`Consec` does not create cross-worker continuity. It slices consecutive windows
from the same sampled batch rows. If row origins are mixed upstream, fix replay
worker ids or source composition first.

### `Zip`

Concatenates batches from multiple sources along the first dimension:

```python
stream = streams.Zip([train_stream, eval_stream])
batch = next(iter(stream))
```

All sources must return matching tree/key structures and compatible shapes
except for the concatenation dimension.

### `Map`

Applies a transformation and forwards save/load:

```python
stream = streams.Map(source, lambda batch: {k: v for k, v in batch.items() if k != 'stepid'})
```

Use `Map` for lightweight key filtering, dtype conversion, or augmentation that
belongs outside the environment.

### `Mixer`

`Mixer` is intended to randomly choose one named source according to weights.
Because stream implementations can be version-sensitive, smoke-test `Mixer`
with a tiny source before depending on it. For robust workflows, prefer an
explicit `Zip` or separate streams unless you have verified `Mixer.__iter__`,
`__next__`, `save()`, and `load()` in the installed package.

## Replay-to-stream recipes

### Stateless replay stream

```python
from embodied.core import streams

train_stream = streams.Stateless(lambda: replay.sample(batch=16, mode='train'))
batch = next(train_stream)
```

### Prefetched replay stream

```python
source = streams.Stateless(lambda: replay.sample(batch=16, mode='train'))
stream = streams.Prefetch(source, amount=2)
stream = iter(stream)
batch = next(stream)
```

### Consecutive windows from a longer sample

```python
long_source = streams.Stateless(lambda: replay.sample(batch=8, mode='train'))
windows = streams.Consec(long_source, length=16, consec=2, prefix=0, strict=False)
windows = iter(windows)
first = next(windows)
second = next(windows)
assert first['consec'].shape == second['consec'].shape
```

For `Consec(length=16, consec=2)`, the source replay length must be at least 32
when `prefix=0`. If using `prefix>0`, source length must cover the additional
context.

## Debugging sampling that never returns

1. Print `len(replay)` before sampling. It must be greater than zero.
2. Confirm each active worker has at least `length` inserted transitions.
3. Confirm the callback is actually registered before `driver(...)` runs.
4. Confirm `driver(...)` was called with positive `steps` or `episodes`.
5. Lower `length` temporarily and rerun the bundled checker in replay mode.
6. If using `online=True`, verify the queue is being filled; normal selector
   items should still exist after enough transitions.

## Debugging worker-stream mixing

Use a diagnostic field during collection:

```python
def add_with_worker(tran, worker):
  tran = dict(tran)
  tran['debug_worker'] = np.int32(worker)
  replay.add(tran, worker=worker)

driver.on_step(add_with_worker)
batch = replay.sample(batch=8)
assert (batch['debug_worker'] == batch['debug_worker'][:, :1]).all()
```

If this assertion fails, transitions were added with the wrong worker id, the
field was overwritten, or downstream stream composition concatenated/mixed rows
in a way that the assertion did not expect.
