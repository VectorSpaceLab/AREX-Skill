# Persistence and evaluation workflows

All examples are bounded and use caller-owned arrays. They do not download
benchmarks, assume a repository root, or write outside an explicit temporary or
output path.

## 1. Safe byte and file round trip

```python
from pathlib import Path
import os
import tempfile
import numpy as np
import faiss

# index is already trained/populated and xq has the same d/metric contract.
def search_pair(a, b, xq, k):
    Da, Ia = a.search(xq, k)
    Db, Ib = b.search(xq, k)
    np.testing.assert_array_equal(Ia, Ib)
    np.testing.assert_allclose(Da, Db, rtol=0, atol=0)

payload = np.asarray(faiss.serialize_index(index), dtype=np.uint8)
if payload.nbytes == 0:
    raise ValueError("empty serialized index")
from_bytes = faiss.deserialize_index(payload)
search_pair(index, from_bytes, xq, k)

# Publish atomically: write in the destination directory, then replace.
out = Path("result.index").resolve()
with tempfile.NamedTemporaryFile(dir=out.parent, prefix=out.name + ".tmp-",
                                 delete=False) as f:
    tmp = Path(f.name)
try:
    faiss.write_index(index, str(tmp))
    if tmp.stat().st_size == 0:
        raise IOError("Faiss wrote an empty index")
    os.replace(tmp, out)
finally:
    tmp.unlink(missing_ok=True)
from_file = faiss.read_index(str(out))
search_pair(index, from_file, xq, k)
```

Do not publish a file until its write and read checks pass. If a process can
crash during publication, use a separate manifest that records dimension,
metric, factory/configuration, `ntotal`, byte size, and a cryptographic hash.
Do not use Python pickle as a substitute for Faiss index I/O when the artifact
crosses a trust boundary.

## 2. Validate the evaluation contract before searching

A metric/shape mismatch is easy to miss because both exact and approximate
indexes can return arrays of the expected rank. Make the contract explicit:

```python
def checked_search(index, xq, k, metric):
    xq = np.asarray(xq)
    if xq.ndim != 2 or xq.shape[1] != index.d:
        raise ValueError(f"query shape {xq.shape} does not match d={index.d}")
    if xq.dtype != np.float32 or not xq.flags.c_contiguous:
        xq = np.ascontiguousarray(xq, dtype="float32")
    if int(index.metric_type) != int(metric):
        raise ValueError(
            f"metric mismatch: index={index.metric_type}, expected={metric}"
        )
    return index.search(xq, k)
```

For a reproducible failure test, create `IndexFlatL2(d)` as the ground-truth
index, call `checked_search` with `METRIC_INNER_PRODUCT`, and expect the
`ValueError`; repeat with `xq[:, :-1]` to test dimension validation. Do not
"fix" a mismatch by comparing distances from different metrics.

## 3. Exact ground truth versus a tiny IVF candidate

Use the same database IDs and preprocessing for both indexes. The following is
an in-memory baseline; replace only the database iterator if it no longer fits
memory.

```python
metric = faiss.METRIC_L2
xt = np.ascontiguousarray(xt, dtype="float32")
xb = np.ascontiguousarray(xb, dtype="float32")
xq = np.ascontiguousarray(xq, dtype="float32")

exact = faiss.IndexFlat(xb.shape[1], metric)
exact.add(xb)
gt_D, gt_I = exact.search(xq, k)

candidate = faiss.index_factory(xb.shape[1], "IVF8,Flat", metric)
candidate.train(xt)
candidate.add(xb)
faiss.ParameterSpace().set_index_parameter(candidate, "nprobe", 2)
D, I = candidate.search(xq, k)

hits = sum(len(set(I[q].tolist()) & set(gt_I[q].tolist()))
            for q in range(xq.shape[0]))
recall = hits / float(xq.shape[0] * k)
precision = hits / float(np.count_nonzero(I != -1))
print({"recall_at_k": recall, "precision_at_k": precision})
```

`IndexFlat` is exact for the selected metric (subject to floating-point
arithmetic). IVF is approximate because it preselects lists; increasing
`nprobe` generally improves recall at more search cost and `nprobe >= nlist`
provides a useful correctness check. A smoke test should report a measured
value, not promise a universal threshold. If a quality gate is needed, pass a
threshold derived from the application and dataset, not from this tiny random
example.

For cosine similarity:

```python
faiss.normalize_L2(xt)
faiss.normalize_L2(xb)
faiss.normalize_L2(xq)
metric = faiss.METRIC_INNER_PRODUCT
```

Normalize every split, including queries and training data, before training
and adding. Never compare normalized-IP ground truth to unnormalized-L2 IVF
output.

## 4. Blocked exact ground truth without downloads

When `xb` is supplied as a trusted local iterator, use a flat index one block at
a time and merge top-k results. The maintained helper is
`faiss.contrib.exhaustive_search.knn_ground_truth`:

```python
from faiss.contrib.exhaustive_search import knn_ground_truth

def blocks(xb, block_size=1024):
    for start in range(0, len(xb), block_size):
        yield np.ascontiguousarray(xb[start:start + block_size], dtype="float32")

gt_D, gt_I = knn_ground_truth(
    np.ascontiguousarray(xq, dtype="float32"),
    blocks(xb, 1024),
    k,
    metric_type=metric,
    ngpu=0,                    # CPU-only, explicit and bounded
)
```

The helper uses an exact flat index and a result heap, offsets block-local IDs,
then resets the block index. Keep `xq`, block size, `k`, and total rows bounded.
A block iterator must preserve row order and dimension; a corrupt or truncated
vector file invalidates every resulting ID.

## 5. fvecs, ivecs, and bvecs files

The TEX-MEX record formats are dimension-prefixed, fixed-width records:
`<int32 dimension><dimension payload values>`. `fvecs` payloads are float32,
`ivecs` payloads are int32, and `bvecs` payloads are uint8. Dimension is stored
per record, but robust readers should verify that all records agree and that
file size is a multiple of `4 + d * itemsize`.

A self-contained bounded reader for a homogeneous local file can be adapted as
follows (it does not fetch data):

```python
from pathlib import Path
import numpy as np

def read_prefixed_vecs(path, kind, max_vectors=None):
    path = Path(path)
    if kind == "fvecs":
        payload_dtype = np.dtype("<f4")
    elif kind == "ivecs":
        payload_dtype = np.dtype("<i4")
    elif kind == "bvecs":
        payload_dtype = np.dtype("u1")
    else:
        raise ValueError("kind must be fvecs, ivecs, or bvecs")
    raw = np.memmap(path, mode="r", dtype=np.uint8)
    if raw.size < 4:
        raise ValueError("vector file has no dimension header")
    d = int(np.frombuffer(raw[:4], dtype="<i4")[0])
    if d <= 0:
        raise ValueError("invalid dimension")
    record = 4 + d * payload_dtype.itemsize
    if raw.size % record:
        raise ValueError("truncated or malformed fixed-width vector file")
    n = raw.size // record
    if max_vectors is not None:
        n = min(n, int(max_vectors))
    records = raw.reshape(-1, record)[:n]
    dims = np.frombuffer(records[:, :4].tobytes(), dtype="<i4")
    if not np.all(dims == d):
        raise ValueError("dimension header changes within file")
    out = np.frombuffer(records[:, 4:].tobytes(), dtype=payload_dtype)
    return out.reshape(n, d).copy()
```

The repository helper has `fvecs_read`, `ivecs_read`, `fvecs_mmap`,
`ivecs_mmap`, `bvecs_mmap`, writers, and bounded `bvecs_iter`. The important
adaptation is to validate headers and bounds rather than relying on a large
benchmark fixture. On big-endian hosts, byteswap integer headers/payloads as
appropriate. Convert float vectors to contiguous float32 before Faiss calls.
Do not interpret `bvecs` bytes as float vectors without an explicit conversion.

## 6. Clustering for a bounded training set

```python
x_train = np.ascontiguousarray(x_train, dtype="float32")
if x_train.ndim != 2 or x_train.shape[0] < k:
    raise ValueError("need at least k training rows with a matching dimension")
km = faiss.Kmeans(
    x_train.shape[1], k,
    niter=5,
    nredo=1,
    seed=123,
    verbose=False,
)
final_error = km.train(x_train)
centroids = np.asarray(km.centroids, dtype="float32").reshape(k, x_train.shape[1])
D_assign, I_assign = km.assign(x_train[: min(32, len(x_train))])
```

Use fixed seeds and fixed thread settings for reproducible smoke artifacts.
For a production index, assess training-set representativeness, objective
progress (`km.obj`), centroid occupancy, and the number of samples per
centroid. Weighted `Clustering.train(..., weights=...)` is a different
contract: weights must be one float32 value per row. Core clustering is CPU
verified; GPU clustering is not.

## 7. Codes and reconstruction quality

For a codec or compressed index that supports standalone coding:

```python
codes = codec.sa_encode(xb)             # uint8, (n, codec.sa_code_size())
xb_hat = codec.sa_decode(codes)         # float32, (n, d)
recon_mse = np.mean((xb - xb_hat) ** 2)
```

Use `codec.reconstruct`/`index.reconstruct_batch` only for IDs supported by
that index. Report reconstruction MSE (or the application metric) separately
from search recall. A lower reconstruction error does not prove better ANN
recall, and exact `IndexFlat` storage should not be used as the expected
reconstruction behavior of a compressed index. Codec construction and code
size constraints belong to the training branch.

## 8. Safe bounded operating-point experiments

For a few explicitly chosen values, a manual loop is easier to bound and audit:

```python
import time
faiss.omp_set_num_threads(1)
rows = min(len(xq), 64)
q = xq[:rows]
gt = exact.search(q, k)[1]
for nprobe in (1, 2, min(8, candidate.nlist)):
    candidate.nprobe = nprobe
    candidate.search(q[: min(4, rows)], k)       # warmup
    t0 = time.perf_counter()
    D, I = candidate.search(q, k)
    elapsed = time.perf_counter() - t0
    hits = sum(len(set(I[i]) & set(gt[i])) for i in range(rows))
    print(nprobe, hits / float(rows * k), elapsed / rows)
```

`ParameterSpace` is useful when the index family exposes its tunable ranges:

```python
crit = faiss.OneRecallAtRCriterion(rows, 1)
crit.set_groundtruth(None, gt)
crit.nnn = k
ps = faiss.ParameterSpace()
ps.initialize(candidate)
# Inspect and cap before running; the default can be much larger than a smoke.
ps.n_experiments = min(int(ps.n_experiments), 8)
ops = ps.explore(candidate, q, crit)
```

`explore` may still perform training-independent searches and timing. Use it
only with small local arrays, a fixed thread count, and a process-level time
budget. Keep Pareto points (`performance`, time, parameter string) rather than
assuming the fastest run is the best operating point.

## 9. OnDisk IVF merge and mmap lifetime

The bulk pattern is:

1. Train an empty IVF index once and write it to a controlled directory.
2. Read that trained index independently for each shard, add a disjoint slice
   with explicit IDs, and write each shard index.
3. Call `faiss.contrib.ondisk.merge_ondisk` with the trained empty index, the
   shard filenames, and a new `ivfdata` path.
4. Write the populated output index only after the merge succeeds.
5. Publish the index, its external `ivfdata`, and a manifest together. On read,
   resolve the external path deliberately, optionally using
   `IO_FLAG_ONDISK_SAME_DIR`.

For a read-mostly artifact, `faiss.read_index(path, faiss.IO_FLAG_MMAP)` can
avoid materializing supported IVF data. `IO_FLAG_MMAP_IFC` is the tested path
for selected `IndexFlatCodes`/HNSW storage. Mmap can lower startup memory but
keeps file-backed pages and leaves the index tied to the file. Close/delete
all index references before deleting or replacing the backing file; on some
platforms the open mapping prevents unlink. Do not mutate a read-only mapping.
