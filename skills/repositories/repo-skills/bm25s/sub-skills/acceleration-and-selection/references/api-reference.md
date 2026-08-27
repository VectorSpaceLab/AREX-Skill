# Acceleration API reference

This reference records the verified public knobs for the `bm25s` revision used
by this skill. It deliberately omits the ordinary BM25 scoring and tokenization
API; route those questions to the sibling operating skills.

## Backend controls on `BM25`

| API | Relevant default | Operational meaning |
|---|---|---|
| `BM25(..., backend="numpy")` | `"numpy"` | NumPy scoring/retrieval path; required CPU baseline. |
| `BM25(..., backend="numba")` | optional | Requires an importable Numba package; raises `ImportError` at construction when unavailable. |
| `BM25(..., backend="auto")` | not the constructor default | Resolves to `"numba"` if the package import succeeded, otherwise `"numpy"`; inspect `retriever.backend`. |
| `BM25(..., csc_backend="numpy")` | `"numpy"` | Pure Python/NumPy CSC arrays; no SciPy requirement. |
| `BM25(..., csc_backend="scipy")` | optional | Uses `scipy.sparse.csc_matrix`; explicit missing SciPy raises `ImportError`. |
| `BM25(..., csc_backend="auto")` | not the constructor default | Resolves to `"scipy"` if SciPy is available, otherwise `"numpy"`; inspect `retriever.csc_backend`. |
| `BM25(..., auto_compile=True)` | `True` | Requests constructor-time Numba compilation when the selected BM25 backend is Numba and the environment guard permits it. For deterministic setup, use `False` and call `compile` explicitly. |

`backend` and `csc_backend` are independent. Numba retrieval can use NumPy
CSC construction, and NumPy retrieval can use a Numba-activated CSC builder if
Numba is explicitly compiled before indexing. Prefer matching the configuration
to the actual bottleneck instead of enabling every optional dependency.

The constructor checks explicit `backend="numba"` and
`csc_backend="scipy"` dependencies. The source does not reject every arbitrary
backend string at construction, so use only the documented values; a typo may
surface later in retrieval or selection rather than at object creation.
Invalid `csc_backend` values are rejected by `build_index_from_ids`/`index`
with `ValueError` and the allowed set `scipy`, `numpy`.

## Compilation and warmup

```python
retriever.compile(activate_numba=True, warmup=False)
retriever.activate_numba_scorer()
retriever.activate_numba_csc()
retriever.warmup_numba_scorer()
retriever.warmup_numba_csc()
```

- `compile` requires Numba even if the retriever was initially configured for
  NumPy. With `activate_numba=True` it replaces the instance scorer and CSC
  builder with JIT wrappers; with `warmup=True` it invokes both dummy warmups.
- `activate_numba_scorer` affects `get_scores` and NumPy-style retrieval that
  calls the instance scorer. The Numba retrieval implementation has its own
  jitted retrieval/scoring path.
- `activate_numba_csc` affects subsequent index construction. Call it before
  `index` if CSC construction is the target; it does not rebuild an existing
  index.
- `warmup_numba_scorer` and `warmup_numba_csc` return early when JIT is disabled
  or Numba is unavailable. `compile` itself raises `ImportError` when Numba is
  unavailable.
- The constructor documents `auto_compile=True` as automatic compilation, but
  the inspected code's guard is sensitive to `NUMBA_DISABLE_JIT`; with that
  variable unset, a runtime probe observed no compiled wrapper. Treat explicit
  `compile` plus a smoke check as the reliable contract. Do not set
  `NUMBA_DISABLE_JIT` when expecting JIT acceleration.

## Retrieval and top-k selection

`BM25.retrieve` has these acceleration-relevant arguments:

```python
retriever.retrieve(
    query_tokens,
    k=10,
    sorted=True,
    return_as="tuple",
    n_threads=0,
    chunksize=50,
    backend_selection="auto",
)
```

`backend_selection` is the selector, not the BM25 scoring backend:

- With `retriever.backend == "numpy"`, `"numpy"` calls
  `bm25s.selection.topk`; `"jax"` calls JAX `lax.top_k`; `"auto"` chooses JAX
  when import initialization succeeded and NumPy otherwise.
- With `retriever.backend == "numba"`, `"auto"` is rewritten to `"numba"`.
  The Numba functional retrieval path rejects any other selector with
  `ValueError`, explaining that `numba` must be selected.
- Numba retrieval ignores `chunksize` and selects its own chunking. Its
  `n_threads=0` path uses one Numba thread; `n_threads=-1` requests all CPUs.
  A positive value sets Numba's thread count for the call and restores the
  previous count afterward.
- Retrieval rejects `k > num_docs` before selection. Keep `k` positive and no
  larger than the number of indexed documents.

### Single-query selectors

```python
from bm25s.selection import topk
scores, indices = topk(scores_1d, k=10, backend="auto", sorted=True)
```

`bm25s.selection.topk` accepts a one-dimensional score array. Valid backends
are `numpy`, `jax`, and `auto`. Invalid names raise:

```text
ValueError: Invalid backend. Please choose from 'numpy' or 'jax'.
```

When JAX is explicitly requested while unavailable, it raises an `ImportError`
with a CPU JAX installation hint. NumPy uses `argpartition`; `sorted=False`
returns the selected items without the final score ordering. JAX's
`jax.lax.top_k` returns descending top-k values and the implementation converts
both outputs back to NumPy arrays; the current JAX path does not use the
`sorted` flag to produce an unsorted result.

The separate `bm25s.numba.selection.topk` accepts only
`backend="numba"`. It uses a Numba heap-based top-k implementation and then
sorts when `sorted=True`. Its own invalid-backend message is:

```text
ValueError: Invalid backend. Only 'numba' is supported.
```

## Availability probes and extras

```python
import bm25s
import bm25s.selection as selection

print(bm25s.NUMBA_AVAILABLE)             # retrieval/compile import status
print(bm25s.SCIPY_AVAILABLE)             # CSC import status
print(selection.JAX_IS_AVAILABLE)        # top-k import/initialization status
```

The metadata-backed installation choices are:

| Need | Extra or direct install | Fallback |
|---|---|---|
| Numba retrieval/compile | `bm25s[core]` or `numba` | `backend="auto"` → NumPy |
| SciPy CSC builder | `bm25s[indexing]` or `scipy` | `csc_backend="auto"` → NumPy |
| JAX top-k | `bm25s[selection]` (`jax[cpu]`) | `backend_selection="auto"` → NumPy |

These are optional CPU paths. A successful import does not prove that a
particular hardware accelerator is present or useful; compare results against
the NumPy baseline on a local fixture first.
