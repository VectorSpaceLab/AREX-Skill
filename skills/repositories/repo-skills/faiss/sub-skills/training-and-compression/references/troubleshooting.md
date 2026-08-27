# Compression troubleshooting and recovery

Keep the original dimension, metric, factory string, training count, package
version, and full exception when diagnosing. Make one repair at a time, rerun
the deterministic smoke, and then rerun the relevant quality check. These
checks assume the required CPU package is installed; optional backend failures
belong to the accelerated sibling.

## Factory or constructor rejects `d`/`M`

**Symptoms:** `d should be a multiple of M`, `dimension mismatch`, or a
factory parse error for `PQ...`.

**Diagnosis:** In `PQ<M>x<nbits>`, the first number is `M` (subquantizers),
not bits. Verify the dimension at every transform boundary:

```python
index = faiss.index_factory(d, "OPQ8_32,PQ8x4")
assert index.d == d
assert faiss.downcast_index(index.index).d == 32  # inspect only after probing
```

For `d=64`, `PQ7`/`PQ7x4` is invalid because `64 % 7 != 0`; use `M=8` or
change the transformed dimension deliberately. For a reduced transform, use
`d_out % M == 0`. Do not patch `index.d`, set `is_trained=True`, or reuse
codebooks after changing dimensions. Reconstruct a fresh index and retrain.

## `add` says the index is not trained

**Cause:** An IVF/PQ/SQ/RQ/AQ/OPQ chain was constructed but `train` was
skipped or the training call did not reach the outer `IndexPreTransform`.

**Recovery:**

1. Verify the training matrix is finite contiguous float32 and has the outer
   dimension.
2. Call `index.train(x_train)` on the outermost index.
3. Check `index.is_trained` and, for a chain, inspect only public nested state
   if necessary.
4. Add vectors with the same original-space dimension.

`BFlat` and some binary indexes are already trained; `BIVF...` is not. Binary
training and add require packed uint8 rows, not float32 arrays.

## Training warns about too few points or fails on clusters

Faiss clustering warns below its default 39 points per centroid and needs at
least one point per centroid. IVF-PQ has coarse centroids plus PQ centroids;
large `nlist`, `M`, or `nbits` can make a supposedly “small” training job
under-supported. Increase representative data, reduce `nlist`/bits, or
explicitly document the smoke as a low-quality fixture. Do not suppress the
warning and report production recall from it.

If training is memory-bound, use a representative bounded sample and record
its size. Faiss can subsample large training sets according to clustering
parameters; this does not make a biased sample representative.

## `PQ` code size or bit interpretation is wrong

Use the object's value rather than a guessed formula:

```python
assert codes.dtype == np.uint8
assert codes.shape[1] == index.sa_code_size()
```

For ordinary PQ, `ceil(M * nbits / 8)` is the payload. Non-byte-aligned codes
pack fields across bytes. `PQ8x4` is 4 bytes, not 8; `PQ8x8` is 8 bytes. RQ/AQ
and RaBitQ can add norm/factor fields, and IVF standalone encodings can include
context. Never slice arbitrary bytes or treat fast-scan blocks as row-major
codes.

## `sa_encode`/`sa_decode` shape or dtype errors

The Python wrapper requires float32 vector rows of shape `(n, d)` for encoding
and contiguous `uint8` code rows of shape `(n, sa_code_size())` for decoding.
Repair with `np.ascontiguousarray`, then assert the exact width. A decoded row
is an approximation for lossy codecs. `IndexIVFPQ`/IVF additive code paths may
need list context internally; prefer the public wrapper and the index's own
`reconstruct` method rather than copying inverted-list bytes.

For RaBitQ, do not use `sa_decode` as an L2 reconstruction oracle. Its public
header warns that the decode is good for IP but not L2; use the search distance
computer and evaluate L2 neighbors independently.

## Binary input has the wrong shape or type

**Symptoms:** assertion/type errors from `IndexBinary`, unexpectedly huge
Hamming distances, or a row-size mismatch.

For dimension `d`, require `d % 8 == 0` and exactly `d // 8` bytes per row:

```python
bits = bits.astype("uint8", copy=False)
codes = np.packbits(bits, axis=1, bitorder="little")
assert codes.shape == (len(bits), d // 8)
assert codes.dtype == np.uint8
```

Do not pass `(n, d)` 0/1 floats or boolean arrays. Use the same packing
convention for database and queries. Binary distances are integer Hamming-like
values and must be compared with a binary exact baseline such as `BFlat`, not
with float L2 distances.

## Invalid fast-scan factory or runtime failure

Fast scan currently targets 4-bit PQ/AQ layouts. Check all of:

- factory has `PQ<M>x4fs` (not `x8fs` for PQ fast scan);
- `d % M == 0`;
- `bbs` is positive and divisible by 32 (`_32`, `_64`, ...);
- the installed package actually exposes the fast-scan class/factory token.

If an explicit conversion from an ordinary `IndexPQ`/`IndexIVFPQ` fails, first
train and add the ordinary index, then convert with a compatible block size.
Compare searches against the ordinary index. A scalar dispatch or unsupported
SIMD level is a build/performance limitation, not permission to change the
code layout manually. If a requested fast-scan path is absent, use ordinary
PQ or route optional backend/build questions to accelerated-and-interoperable.

## Recall is poor after compression

Separate three effects:

1. **Candidate loss:** IVF coarse assignment or too-small `nprobe` did not
   visit the true neighbor.
2. **Code distortion:** PQ/SQ/RQ/AQ reconstruction changed distances.
3. **Search approximation:** fast scan, polysemous filtering, or an additive
   lookup/search mode changed the ranking.

Build an exact `IndexFlatL2`/`IndexFlatIP` baseline with the same metric and
query normalization. Increase `nprobe` first for candidate loss; then compare
more bits, a different `M`, OPQ, or SQ/PQ storage. If the candidate is present
but ranked poorly, use a measured refinement stage. Refinement cannot recover a
candidate excluded by IVF, and it does not repair insufficient training.

Do not compare recall from different train splits, dimensions, normalization,
`nprobe`, or `k_factor` and call it a codec result. Route ground truth and
repeatable measurements to persistence-and-evaluation.

## Reconstruction differs from the input

Lossy codecs intentionally reconstruct centroids/codebook approximations. Use
per-vector reconstruction error as a separate metric; neighbor recall may be
acceptable even when error is not, and vice versa. With transforms, output is
in the transform's space until the wrapper applies a supported reverse path.
PCA reduction, normalization, and some generic transforms are not exactly
invertible. Check whether `reverse_transform` is supported before promising
original-space restoration.

For binary indexes, reconstruction returns the stored packed bytes (when that
index implements reconstruction), not float vectors. For RaBitQ L2, follow the
special decode limitation above.

## Metric or normalization mismatch

PQ training is L2-oriented even when an index searches inner product. For
cosine-like workloads, normalize database and query vectors consistently and
use the intended inner-product metric or normalization transform. Verify the
metric on the exact baseline and compressed index. Do not change metric after
training and assume the codebook remains optimal.

## Unexpected memory or slow training

Account separately for:

- training centroids and temporary clustering tables;
- per-vector code payload;
- IVF IDs, list offsets, and coarse quantizer;
- transform state (OPQ/PCA matrices);
- refinement storage and graph/list overhead;
- additive beam/LUT workspaces and fast-scan padded blocks.

Lower `nbits`, `M`, `nlist`, training sample size, or additive beam only after a
bounded quality check. Fast scan may reduce search compute but introduces
blocked layout/padding and build-dependent SIMD behavior. Do not use benchmark
scripts or download datasets as a first diagnostic; the bundled smoke is
intentionally tiny and deterministic.

## Optional backend or SIMD claim cannot be reproduced

The required inspection facts cover CPU `faiss-cpu` 1.15.0 with AVX2. CUDA
hardware being visible does not mean CUDA Faiss symbols are installed. Probe
`faiss.get_num_gpus()` and the optional classes in the accelerated sibling;
record an unavailable backend as unverified and use the CPU path. Do not
install packages, download data, or claim cuVS/ROCm/Metal/SVS behavior from
this branch's smoke.
