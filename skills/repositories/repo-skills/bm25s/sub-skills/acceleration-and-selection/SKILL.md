---
name: acceleration-and-selection
description: "Use optional Numba retrieval and CSC acceleration, NumPy/JAX top-k
  selection, and diagnose dependency or backend fallbacks in bm25s."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---
# Acceleration and selection

Use this route when a local `bm25s` index needs optional Numba scoring/retrieval,
Numba-assisted CSC construction, NumPy/JAX top-k selection, or a diagnosis of
backend and optional-dependency behavior. Keep the ordinary indexing/retrieval
recipe in the core route; this route supplies the acceleration choices that are
safe to add to it.

## Make the backend decision explicit

- The required path is CPU NumPy: `BM25(backend="numpy",
  csc_backend="numpy")`, followed by `retrieve(...,
  backend_selection="numpy")`. The base package requires NumPy; optional speed
  packages are not a runtime prerequisite.
- `backend` selects scoring/retrieval execution. `"numba"` requires Numba;
  `"auto"` resolves to Numba when the import is available and otherwise to
  NumPy. The resolved value is stored in `retriever.backend` at construction.
- `csc_backend` selects index construction: `"numpy"` is the dependency-light
  default, `"scipy"` uses `scipy.sparse.csc_matrix`, and `"auto"` resolves to
  SciPy when SciPy imports successfully and otherwise to NumPy. This choice is
  made while constructing the index, not while selecting top-k results.
- `backend_selection` is a separate top-k selector. For a NumPy BM25 backend,
  `"numpy"`, `"jax"`, and `"auto"` are meaningful. `"auto"` uses JAX when
  `bm25s.selection.JAX_IS_AVAILABLE` is true and NumPy otherwise. JAX is a CPU
  option here; this skill makes no CUDA or GPU-performance promise.
- For a Numba BM25 backend, retrieval internally maps
  `backend_selection="auto"` to `"numba"`; the Numba retrieval path requires
  `backend_selection="numba"`. Do not combine `backend="numba"` with
  `backend_selection="jax"` or `"numpy"`.

The complete parameter and error table is in
[references/api-reference.md](references/api-reference.md). Use the bounded
local checker at [scripts/numba_smoke.py](scripts/numba_smoke.py) before
benchmarking or changing a production configuration.

## Install only what the chosen path needs

```bash
pip install bm25s                 # NumPy base path
pip install "bm25s[core]"         # project core extras, including Numba
pip install "bm25s[indexing]"      # SciPy CSC option
pip install "bm25s[selection]"     # CPU JAX top-k option
```

The package metadata also exposes `numba`, `scipy`, and `jax[cpu]` through the
corresponding extras. `full` combines extras, but is not required for this
route. Install into the same interpreter that imports `bm25s`; report the
actual availability flags rather than assuming that an extra was installed.

## Baseline, Numba, and selector recipes

Start with a baseline when correctness or portability matters:

```python
retriever = bm25s.BM25(backend="numpy", csc_backend="numpy")
retriever.index(corpus_tokens, show_progress=False)
results = retriever.retrieve(
    query_tokens, k=10, backend_selection="numpy", show_progress=False
)
```

For CPU Numba retrieval and optional Numba CSC construction, make compilation
an explicit decision:

```python
retriever = bm25s.BM25(
    backend="numba", csc_backend="numpy", auto_compile=False
)
retriever.compile(activate_numba=True, warmup=False)
retriever.index(corpus_tokens, show_progress=False)
results = retriever.retrieve(
    query_tokens, k=10, backend_selection="numba", show_progress=False
)
```

Call `compile` before `index` when Numba CSC construction should be used; call
it after loading an existing index when only retrieval scoring needs activation.
`warmup=True` runs small dummy CSC and scorer calls to pay JIT compilation before
the first real request. The first call can still have signature/cache overhead,
and Numba is CPU-only in this operating contract. See
[references/numba-workflows.md](references/numba-workflows.md) for the timing,
thread, and fallback decisions.

For NumPy scoring with optional JAX selection:

```python
retriever = bm25s.BM25(backend="numpy", csc_backend="numpy")
retriever.index(corpus_tokens, show_progress=False)
results = retriever.retrieve(
    query_tokens, k=10, backend_selection="jax", show_progress=False
)
```

Use `backend_selection="auto"` only when a JAX-versus-NumPy choice is
acceptable. `bm25s.selection.topk` accepts one-dimensional score arrays and
raises `ValueError` for an invalid selector; an explicit JAX request raises
`ImportError` when JAX is unavailable. The Numba selector is a separate
`bm25s.numba.selection.topk` API and accepts only `backend="numba"`.

## Compile and fallback rules

- `auto_compile` is a constructor control and defaults to `True`, but explicit
  `compile(...)` is the reproducible choice when relying on JIT activation.
  This revision's constructor guard is environment-sensitive; with
  `NUMBA_DISABLE_JIT` unset, inspection observed no automatic compiled wrapper
  despite the default. Do not infer compilation from the constructor flag;
  inspect or run a smoke retrieval.
- If `NUMBA_DISABLE_JIT` is set, the scorer activation/warmup path is skipped.
  Unset it when JIT execution is intended. Keep `auto_compile=False` for
  predictable setup and compile deliberately.
- Missing Numba with `backend="auto"` is a normal fallback to NumPy. Missing
  Numba with `backend="numba"` or `compile(...)` is an actionable `ImportError`.
- Missing SciPy with `csc_backend="auto"` falls back to NumPy. Explicit
  `csc_backend="scipy"` raises `ImportError`.
- Missing JAX with selector `"auto"` falls back to NumPy. Explicit `"jax"`
  raises `ImportError`; an invalid selector raises `ValueError`.
- Do not present optional backends as CUDA support. If a dependency emits a
  GPU-availability warning but imports its CPU implementation, record that as
  CPU execution rather than claiming accelerator coverage.

For install/import, data/configuration, API/CLI, and workflow-specific failures,
use [references/troubleshooting.md](references/troubleshooting.md). Do not use
Hub/BEIR network examples as acceleration tests; keep checks local and bounded.
