# Compression API and representation reference

This is a compact operating reference for the verified CPU Python package. It
records public contracts rather than implementation details. Probe the installed
package before relying on a newer codec or factory token.

## Array and lifecycle contracts

| Path | Training/add/search input | Code representation | Distance output |
|---|---|---|---|
| Float index (`IndexPQ`, `IndexScalarQuantizer`, IVF variants) | C-contiguous `float32`, shape `(n, d)` | `uint8` codes internally; `sa_encode` returns `(n, sa_code_size())` | `float32` distances and `int64` labels |
| Binary index (`IndexBinary*`) | C-contiguous `uint8`, shape `(n, d // 8)` | One packed byte row per vector; `code_size == d // 8` | `int32` Hamming-like distances and `int64` labels |

Python wrappers validate dimensions and reject non-`uint8` binary code arrays;
use `np.ascontiguousarray` explicitly when data came from a slice. Float
wrappers convert ordinary array-like inputs to contiguous float32, but making
the conversion explicit prevents accidental copies and metric/dtype confusion.
Search returns `(D, I)` with shape `(nq, k)`. Missing float results use label
`-1`; binary results use the corresponding binary wrapper convention.

A trained codec has `is_trained == True`. For an untrained `IndexPQ`,
`IndexScalarQuantizer`, `IndexIVFPQ`, `IndexIVFScalarQuantizer`, RQ/AQ, OPQ,
or transform chain, the safe lifecycle is:

```python
index = faiss.index_factory(d, description, metric)
index.train(x_train)       # finite float32 representative sample
assert index.is_trained
index.add(x_database)
D, I = index.search(x_query, k)
```

`IndexBinaryFlat`, `IndexBinaryHNSW`, and some other binary paths do not need
training. `IndexBinaryIVF`/`BIVF...` does: train and add packed `uint8` rows.
Never add production vectors before training merely because the constructor
succeeded.

## PQ and code-size rules

For `ProductQuantizer(d, M, nbits)` and `IndexPQ(d, M, nbits)`:

- `M > 0` and **`d % M == 0`**; each subvector has `dsub = d // M`.
- `ksub = 2 ** nbits`; the CPU implementation rejects `nbits > 24` as not
  practical. Use small tested values (commonly 4 or 8; 1--16 is a practical
  planning range) unless a target build proves another value.
- Packed code size is `ceil(M * nbits / 8)` bytes per vector. For example,
  `PQ8x4` is 4 bytes and `PQ8x8` is 8 bytes. The code size is not the original
  `d * 4` bytes and excludes IDs and IVF list bookkeeping.
- PQ centroids are learned by k-means per subvector. The error objective is
  L2-oriented even though PQ indexes can search L2 or inner product.
- `do_polysemous_training` is a training/search option, not a substitute for
  enough representative data. The `np` factory suffix disables the default
  polysemous training behavior.

`IndexIVFPQ(quantizer, d, nlist, M, nbits, metric)` adds a coarse quantizer
and stores residual PQ codes by default. Its effective byte footprint also
contains list IDs/coarse assignment and inverted-list overhead. `nprobe` is a
search-time candidate control; it does not alter the trained code size. For
inner product, ensure the chosen metric is passed consistently and validate
recall separately.

Useful factory forms include:

```text
PQ8x4                 # flat PQ; x4 means 4 bits per subquantizer
PQ8                   # flat PQ with the default 8 bits
PQ8x4np               # flat PQ, without polysemous training
IVF64,PQ8x8           # residual IVF-PQ (coarse + PQ)
IVF64,PQ8x4np         # IVF-PQ without polysemous training
```

`IVF...` factory dimensions apply to the current transformed dimension. An
`OPQ...` or `PCA...` prefix can change that dimension before the codec.

## Scalar quantization

`IndexScalarQuantizer(d, qtype, metric)` and `IndexIVFScalarQuantizer` encode
components rather than subvectors. Common factory/storage choices are:

| Factory | Approximate payload per vector | Use/qualification |
|---|---:|---|
| `SQ8` | `d` bytes | 8 bits/component, general low-error baseline |
| `SQ4` | `ceil(d / 2)` bytes | 4 bits/component, more error |
| `SQ6` | `ceil(6*d / 8)` bytes | 6 bits/component |
| `SQfp16`, `SQbf16` | `2*d` bytes | half/bfloat storage; verify package support |
| `SQ8_direct`, signed variants | approximately `d` bytes | direct integer-domain use, not generic float compression |

The exact `code_size` property is authoritative, especially for less common
quantizer types. SQ training learns ranges/levels from representative data.
Uniform and TQ/EDEN variants have additional data-distribution and build
considerations; treat them as opt-in and smoke-test them.

## Residual and additive codecs

`ResidualQuantizer` represents a vector as a sum of codebook entries selected
level by level; `AdditiveQuantizer` is the common base. Unlike PQ, additive
codebooks are summed rather than concatenated. `IndexResidualQuantizer`,
`IndexLocalSearchQuantizer`, product RQ/LSQ, and their IVF variants expose
variable `nbits` per level and search-type choices such as decompression or
lookup-table modes.

For a vector of additive levels with bit counts `nbits[i]`, the nominal packed
index portion is `ceil(sum(nbits) / 8)` bytes; norm/factor fields may add bytes
for norm-aware modes and RaBitQ-like formats. Use the object's
`sa_code_size()`/`code_size`, not a hand formula, before allocating buffers.
Training can use beam search and consume substantial memory; lower beam or
batch size only after recording the quality consequence.

`IndexRaBitQ(d, metric, nb_bits)` supports 1-bit and multi-bit forms in the
verified API (the repository tests cover 1--9). Its code includes auxiliary
factors, so do not estimate its size as simply `ceil(d * nb_bits / 8)`.
`IndexRaBitQ` can search with quantized queries (`qb > 0`) or an fp32 query
path (`qb == 0`); fast-scan RaBitQ variants require quantized queries. For L2,
follow the class warning: `sa_decode()` is not a reliable reconstruction
oracle; use the distance/search implementation.

## Transforms and composition

`IndexPreTransform(transform, index)` applies transforms at train, add, and
search time. Train the outer chain on original-space float32 data. The nested
codec must receive the transform's `d_out`.

- `OPQMatrix(d, M[, d2])` learns a rotation intended to align dimensions for
  PQ. With `d2` omitted, output dimension is normally `d`; if using a reduced
  output dimension, choose the downstream codec's `M` against `d2`, not the
  original `d`.
- `OPQ16,PQ16x8` means train OPQ and then PQ in the transformed space.
- `OPQ16_64,PQ16x8` changes the codec input to 64 dimensions; 64 must be
  divisible by 16.
- `PCA`, `RR`, `HR`, normalization, and other transforms have their own
  reversible/irreversible semantics. A reverse transform may be unavailable
  or approximate; a successful `reconstruct` is not proof that the original
  vector is recoverable.

Factory parsing is compositional and parentheses matter, for example
`IVF32(PQ8),Flat` makes a PQ coarse quantizer while `IVF32,Flat,Refine(PQ8)`
uses PQ as a refinement storage choice. Route ownership and refinement behavior
to the composition sibling.

## Fast scan

`IndexPQFastScan` and `IndexIVFPQFastScan` use blocked packed codes and SIMD
lookup tables. The supported fast-scan PQ form is **4-bit**; the build block
size (`bbs`) must be a positive multiple of 32, with 32 as the usual default.
The final block can contain padding entries. Examples:

```text
PQ16x4fs
PQ16x4fs_64
IVF32,PQ16x4fs
IVF32,PQ16x4fsr_64       # residual mode
```

The `r` suffix changes residual behavior; it does not mean a generic
reconstruction refinement. Fast scan changes layout and speed, and may lose
some quality depending on implementation/search settings. SIMD dispatch is
build/CPU dependent; a scalar fallback or unavailable optimized kernel is
not a correctness failure. Compare results with the non-fast-scan codec when
changing `bbs` or implementation knobs.

## Standalone encode/decode and reconstruction

For any float `Index` implementing the standalone codec interface:

```python
codes = index.sa_encode(x.astype("float32", copy=False))
assert codes.dtype == np.uint8
assert codes.shape == (len(x), index.sa_code_size())
restored = index.sa_decode(codes)
```

The wrappers require exact code width and `uint8` dtype. `IndexPQ` and SQ
reconstruct approximate vectors. IVF codecs may require list context for
internal encodings; use the public `sa_*` methods or `reconstruct` wrapper,
not guessed byte slicing. `search_and_reconstruct` returns approximations for
lossy storage and may be unavailable for an individual index family.

## Binary/Hamming path

Binary indexes are a distinct API, not a float PQ shortcut:

```python
d = 64
bits = (rng.randint(0, 2, size=(n, d))).astype("uint8")
xb = np.packbits(bits, axis=1, bitorder="little")
index = faiss.index_binary_factory(d, "BFlat")
index.add(xb)
D, I = index.search(xb[:2], 4)  # D is int32 Hamming distance
```

Use a packed `(n, d // 8)` `uint8` array. `BFlat` is exact Hamming search;
`BIVF<nlist>` trains a binary coarse quantizer and searches selected lists;
`BHNSW<M>` is a binary graph; `BHash<b>` and `BHash<n_hash>x<b>` are hash
variants. `IDMap`/`IDMap2` wrappers are supported by the binary factory, but
ID ownership/filtering belongs to composition-and-filtering.

Binary factory examples:

```text
BFlat
BIVF16
BIVF16_BHNSW32
BHNSW16
BHash12
BHash5x6
IDMap2,BFlat
```

Binary distances are integer Hamming-like values, and binary reconstruction
returns packed bytes. Do not compare binary distances directly to float L2 or
inner-product distances.
