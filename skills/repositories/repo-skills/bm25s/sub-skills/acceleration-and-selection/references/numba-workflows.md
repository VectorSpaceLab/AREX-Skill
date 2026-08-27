# Local acceleration workflows

All workflows in this reference are local and CPU-scoped. They use an already
tokenized local corpus/query fixture; they do not download BEIR data, access a
Hugging Face repository, or require a CUDA runtime.

## 1. Establish a NumPy reference first

Use the required dependency-light route to establish document IDs, scores, and
result ordering:

```python
import bm25s

reference = bm25s.BM25(backend="numpy", csc_backend="numpy")
reference.index(corpus_tokens, show_progress=False)
expected = reference.retrieve(
    query_tokens, k=3, backend_selection="numpy", show_progress=False
)
```

Keep the same token IDs, `k`, `sorted`, and weight mask when comparing an
optional backend. Exact floating-point equality is normally observed for the
small compatible fixtures in the repository tests, but use score tolerances for
larger or mixed-dtype comparisons and compare document IDs as the main
correctness signal.

## 2. Numba retrieval with deliberate compilation

```python
retriever = bm25s.BM25(
    corpus=corpus_records,
    backend="numba",
    csc_backend="numpy",
    auto_compile=False,
)
retriever.compile(activate_numba=True, warmup=False)
retriever.index(corpus_tokens, show_progress=False)
results = retriever.retrieve(
    query_tokens,
    corpus=corpus_records,
    k=3,
    backend_selection="numba",
    show_progress=False,
)
```

Compile before indexing when the Numba CSC builder should be used. Compile
after `BM25.load(...)` when the saved CSC arrays already exist and only scoring
needs JIT activation. The Numba functional retrieval path is batch-oriented,
ignores `chunksize`, and uses `n_threads` to control Numba threads. Start with
`n_threads=0` for a deterministic single-thread smoke test, then try a bounded
positive value for a workload measurement.

`backend="numba"` is not a portable fallback setting: construction fails when
Numba cannot import. Use `backend="auto"` when a NumPy fallback is acceptable,
and print the resolved `retriever.backend` before interpreting timings.

## 3. Warmup choice

`compile(activate_numba=True, warmup=True)` runs both
`warmup_numba_csc()` and `warmup_numba_scorer()` on tiny synthetic arrays. This
moves some first-use JIT cost into setup and is useful for latency-sensitive
services. `warmup=False` keeps setup shorter and measures a more realistic cold
start, but the first index/retrieval call may pay compilation overhead. The
first actual call can still specialize a new dtype or array signature.

Use this decision table:

| Situation | Choice |
|---|---|
| Portable local check | `backend="numpy"`, no compile |
| Throughput run with Numba | explicit `compile`, then warm up if setup is amortized |
| Latency-sensitive service | explicit compile with `warmup=True` and a startup health check |
| JIT prohibited by deployment | NumPy backend, or set `NUMBA_DISABLE_JIT` and do not claim acceleration |
| Reused saved index | load, then compile scorer; CSC warmup is unnecessary unless rebuilding |

The constructor's `auto_compile=True` is not a sufficient readiness check in
this revision: the environment-sensitive guard observed during inspection did
not create compiled wrappers when `NUMBA_DISABLE_JIT` was unset. Explicit
compile and a bounded smoke test are safer than assuming the default did work.

## 4. `backend="auto"` and dependency fallbacks

```python
retriever = bm25s.BM25(
    backend="auto",
    csc_backend="auto",
    auto_compile=False,
)
print(retriever.backend, retriever.csc_backend)
```

Resolution happens at construction. It is not a per-query health check and it
does not retry a failed import later. Record the two resolved strings and the
availability flags before benchmarking:

```python
print(
    bm25s.NUMBA_AVAILABLE,
    bm25s.SCIPY_AVAILABLE,
    bm25s.selection.JAX_IS_AVAILABLE,
)
```

A missing Numba package selects NumPy for `backend="auto"`; a missing SciPy
package selects NumPy for `csc_backend="auto"`. JAX is selected separately by
`backend_selection="auto"` only on the NumPy retrieval path. An installed JAX
CPU package is still CPU execution and is not evidence of CUDA support.

## 5. NumPy scoring plus JAX top-k

```python
retriever = bm25s.BM25(backend="numpy", csc_backend="numpy")
retriever.index(corpus_tokens, show_progress=False)
results = retriever.retrieve(
    query_tokens, k=3, backend_selection="jax", show_progress=False
)
```

This requires JAX to import and initialize. If it is absent, choose
`backend_selection="numpy"` or install the CPU selection extra. The lower-level
selector is useful for an isolated check:

```python
scores, indices = bm25s.selection.topk(
    one_query_scores, k=3, backend="jax", sorted=True
)
```

The current JAX implementation always calls `jax.lax.top_k`, converts the
result to NumPy, and returns descending values; do not depend on
`sorted=False` to create an unsorted JAX result.

## 6. SciPy versus NumPy CSC construction

Use `csc_backend="numpy"` when avoiding SciPy or when Numba will dominate the
indexing cost. Use explicit `"scipy"` only after a local import check:

```python
retriever = bm25s.BM25(backend="numpy", csc_backend="scipy")
retriever.index(corpus_tokens, show_progress=False)
```

`"auto"` chooses SciPy when available. The resulting BM25 score representation
still contains NumPy-compatible `data`, `indices`, and `indptr` arrays; the
choice is about construction, not a different retrieval result contract.

## 7. What not to benchmark here

Do not turn the networked Numba/Hugging Face or BEIR examples into bundled
runnable helpers. They require remote data, credentials or downloads, obscure
which dependency failed, and are outside the CPU-only smoke contract. If a
large benchmark is desired, first pass the local smoke check, then have the
caller explicitly approve data acquisition and a separate benchmark workflow.
