# Training, compression, and comparison workflows

These recipes are deliberately small enough to adapt into a local check. They
are not benchmark protocols and download no data. Use a held-out query set and
an exact float baseline for any real quality claim; route evaluation details to
the persistence sibling.

## 1. Establish a representative training set

1. Convert source vectors to finite contiguous `float32` with shape `(n, d)`.
   Reject NaNs/Infs and a dimension mismatch before constructing the index.
2. Reserve a representative training slice. It should cover the data
   distribution, not merely be the first few rows. Keep database and queries
   separate where possible.
3. Count the coarse and codec centroids. Faiss clustering defaults to a
   warning threshold of 39 points per centroid and can subsample above 256
   points per centroid; fewer than one point per centroid is invalid. This is
   a training-quality guard, not a promise that a tiny smoke will fail.
4. Train the complete outer index once, then check `index.is_trained` and
   `index.ntotal` after adding. Do not reuse a trained index with a new
   dimension, metric, `M`, or codebook.

For an `IVF<nlist>,PQ<M>x<nbits>` index, the coarse stage has `nlist`
centroids and each PQ subquantizer has `2**nbits` centroids. Increase the
training sample when either count is large. Do not infer that increasing
`nprobe` can repair poorly trained centroids.

## 2. Select a codec from an explicit budget

Start with a table, not a factory guess:

| Candidate | Payload rule | Main quality/compute lever | Typical reason to choose |
|---|---:|---|---|
| `SQ8` | `d` bytes | scalar levels and training distribution | simple, moderate compression |
| `SQ4` | `ceil(d/2)` bytes | lower bits versus quantization error | tighter memory budget |
| `PQ<M>x<nbits>` | `ceil(M*nbits/8)` bytes | `M`, bits, transform, training | flexible product code |
| `IVF<nlist>,PQ...` | PQ payload plus IVF IDs/listing | `nlist`, `nprobe`, codec bits | candidate pruning plus compression |
| `RQ`/`LSQ` family | object `code_size` | levels, per-level bits, beam/search type | additive residual approximation |
| `RaBitQ` | object `code_size` | `nb_bits`, query quantization, metric path | binary-like compact high-dimensional code |
| `BFlat` | `d/8` bytes | none; exact Hamming | packed binary data and exact Hamming |

For a fixed payload, more PQ subquantizers reduce `dsub` and often improve
local modeling, while more bits increase codebook cardinality and training
cost. Neither monotonic quality nor a universal best `M` is guaranteed. Check
`d % M == 0`, then record code width, training time, search candidates, and
held-out recall.

## 3. Build an IVF-PQ/SQ index safely

```python
import faiss
import numpy as np

xtrain = np.ascontiguousarray(xtrain, dtype="float32")
xb = np.ascontiguousarray(xb, dtype="float32")
xq = np.ascontiguousarray(xq, dtype="float32")
d = xtrain.shape[1]
index = faiss.index_factory(d, "IVF32,PQ8x4", faiss.METRIC_L2)
index.train(xtrain)
if not index.is_trained:
    raise RuntimeError("codec did not finish training")
index.add(xb)
index.nprobe = 4
D, I = index.search(xq, 10)
```

Use `IVF32,SQ8` or `IVF32,SQ4` when scalar quantization is the intended
storage. The coarse quantizer, codec, and query metric must agree. For a
non-residual PQ scan, use the factory/class variant explicitly and compare it
with residual mode; the `r` fast-scan suffix is not a general option for all
PQ forms.

If using an explicit constructor, keep the coarse quantizer alive for the
index's ownership contract and configure ownership as documented by the
composition sibling. This branch does not prescribe custom quantizer lifetime
or ID wrappers.

## 4. Compose OPQ with a codec

Use one complete chain so the same transform is trained and applied to train,
add, and query data:

```python
index = faiss.index_factory(d, "OPQ8_32,PQ8x4", faiss.METRIC_L2)
index.train(xtrain)
index.add(xb)
D, I = index.search(xq, 10)
```

Here the transform output is 32 dimensions and `M=8`, so the downstream PQ
has `dsub=4`. For `OPQ8,PQ8x4`, the output remains `d`; for a reduced `OPQ`,
recheck divisibility against the output. Compare OPQ against the same PQ
without OPQ using identical train/database/query splits. OPQ is trained and
may be expensive; it is not a free preprocessing step. A lossy or reduced
transform can make reverse reconstruction approximate or unavailable.

For normalization/cosine-like workflows, choose and document whether the
normalization transform is part of the chain and measure in the normalized
space. Do not silently compare normalized and unnormalized baselines.

## 5. Encode, decode, and inspect a codec

```python
codes = index.sa_encode(xb[:8])
expected = index.sa_code_size()
if codes.dtype != np.uint8 or codes.shape != (8, expected):
    raise ValueError("unexpected standalone code buffer")
xb_hat = index.sa_decode(codes)
```

Use the object's reported width. PQ/SQ/RQ/AQ decoded vectors are lossy.
`IndexIVFPQ` internal list codes can include context; do not treat the
standalone bytes as a portable hand-written format. For search-result
reconstruction use the public `reconstruct`/`search_and_reconstruct` wrapper
and report reconstruction error separately from neighbor recall. For RaBitQ,
follow the L2 caveat in the API reference and use search distance computation
rather than claiming `sa_decode` is an L2 inverse.

## 6. Fast-scan stage

Start with a normal trained `PQ<M>x4` or IVF-PQ index, then use a factory
variant or the explicit fast-scan class when its constraints hold:

```python
fast = faiss.index_factory(d, "PQ8x4fs_32", faiss.METRIC_L2)
fast.train(xtrain)
fast.add(xb)
D, I = fast.search(xq, 10)
```

`M` must divide `d`; 4 bits are required for the PQ fast-scan family; `bbs`
must be a positive multiple of 32. Fast scan packs blocked codes and can pad
the last block, so its packed layout is not a row-major database-code file.
Use a non-fast-scan PQ with the same training data as the correctness
reference. SIMD level, build options, and CPU dispatch can change speed and
implementation; do not report a speedup without a controlled measurement.

For `IndexRefineFlat` or another refinement storage, route construction and
ownership to [composition-and-filtering](../../composition-and-filtering/SKILL.md).
The quality pattern is: compressed index returns `k * k_factor` candidates,
then refinement reranks them with a more accurate storage. Pick `k_factor`
from a measured recall/latency curve; it does not remove the need to train the
base codec.

## 7. Residual/additive/RaBitQ decision

Use RQ/AQ when summing codebook contributions is preferable to PQ's fixed
subvector partition. Start with a small uniform bit vector, inspect the
object's `code_size`, and train on representative data. Variable per-level
bits and beam search change both memory and training time. For large beams,
reduce batch size or beam only with a recorded quality check.

Use RaBitQ when its compact binary-like representation and supported metric
path fit the workload. Select `nb_bits` within the installed package's
supported range, inspect `code_size`, and test `qb`/centered behavior. Do not
claim that the byte layout is interchangeable with `IndexBinary`, and do not
use unverified GPU/SIMD variants as a CPU result.

## 8. Binary/Hamming workflow

```python
d = 64
rng = np.random.RandomState(7)
bits = rng.randint(0, 2, size=(128, d), dtype="uint8")
xb = np.packbits(bits, axis=1, bitorder="little")
index = faiss.index_binary_factory(d, "BIVF8")
index.train(xb[:64])
index.add(xb[64:])
D, I = index.search(xb[:2], 4)
assert D.dtype == np.int32
```

`BFlat` needs no training. `BIVF...` does. `d` must be divisible by eight and
all rows must have exactly `d // 8` bytes. Search distance is integer Hamming;
use a binary exact baseline (`BFlat`) rather than a float L2 index. Binary
factory wrappers, IDs, and selectors have separate ownership/support rules;
route those details to composition-and-filtering.

## 9. Difficult repair and comparison cases

### Repair an invalid `IVF32,PQ7` request

Given `d=64`, `IVF32,PQ7` means **M=7**, not seven bits. Since `64 % 7 != 0`,
the PQ constructor must reject it. Repair with one of:

- `IVF32,PQ8x4` or `IVF32,PQ8x8` when eight subquantizers fit the memory and
  quality budget; or
- `IVF32,PQ7x4` only after changing the transformed dimension to a multiple
  of seven (for example with a deliberate dimension transform), then retrain
  and remeasure.

Do not “fix” it by changing `d` metadata or by setting `is_trained=True`.
For `d=64`, `IVF32,PQ8x4` has a 4-byte PQ payload; `nlist=32` and `nprobe` are
separate coarse/search choices.

### Compare PQ versus SQ and stage refinement

For the same data, metric, and train split:

1. Build `PQ8x4`, `SQ4`, and an exact `Flat` baseline.
2. Record payload bytes/vector from `sa_code_size()` or `code_size`, plus
   index-level overhead separately.
3. Search the same held-out queries and compute recall@k against `Flat`.
4. If PQ has an acceptable candidate recall but poor final precision, put
   `IndexRefineFlat` (or a measured SQ refinement storage) around the trained
   base and increase candidate factor in small steps.
5. If the base misses the true neighbor, refinement cannot recover it. Increase
   IVF `nprobe`, use a less aggressive codec, or retrain before changing the
   refinement stage.

Use [persistence-and-evaluation](../../persistence-and-evaluation/SKILL.md) for
exact ground truth and repeatable metrics. Never present a memory number that
omits IVF IDs, graph links, refinement storage, or transform state when those
objects are deployed.
