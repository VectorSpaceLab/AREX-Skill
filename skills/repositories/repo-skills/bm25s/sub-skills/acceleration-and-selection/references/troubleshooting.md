# Acceleration and selection troubleshooting

Use the smallest local fixture that reproduces the failure. First record the
interpreter, `bm25s.__version__`, and these three flags:

```python
import bm25s
import bm25s.selection as selection
print(bm25s.__version__)
print(bm25s.NUMBA_AVAILABLE, bm25s.SCIPY_AVAILABLE)
print(selection.JAX_IS_AVAILABLE)
```

Do not infer backend availability from a package manager lockfile alone. The
flags are set by the imports used by the installed package.

## Install and import failures

### `bm25s` imports, but an optional extra does not

The base install needs NumPy. Use the same Python executable for the package
and the optional dependency:

```bash
python -m pip install bm25s
python -m pip install "bm25s[core]"       # Numba path
python -m pip install "bm25s[indexing]"   # SciPy CSC path
python -m pip install "bm25s[selection]"  # CPU JAX selector
```

If an environment already has a different NumPy/Numba/SciPy/JAX ABI, repair or
recreate that environment rather than suppressing the import error. A clean
`ImportError` is expected to make `backend="auto"` or
`csc_backend="auto"` fall back; unrelated binary or runtime exceptions need
normal environment diagnosis.

### JAX prints a GPU warning

The selection implementation imports JAX and initializes a tiny `lax.top_k`
call. A warning that no CUDA-enabled `jaxlib` is present is compatible with
CPU JAX operation. This route is explicitly CPU-only: do not convert that
warning into a CUDA promise or a GPU benchmark claim.

### The dependency imports in a shell but not in the application

Check `python -c "import bm25s, numba, scipy"` (or the corresponding JAX
command) using the exact interpreter that launches the application. Do not
mix a system `pip` with a conda/venv Python. The local checker
[`scripts/numba_smoke.py`](../scripts/numba_smoke.py) prints a dependency
summary without downloading anything.

## Optional-dependency and fallback failures

### `backend="numba"` raises `ImportError`

This is the explicit required-backend gate. Install Numba in the active
interpreter, or change to `backend="numpy"`. If portability is more important
than a hard requirement, use `backend="auto"` and report the resolved
`retriever.backend`; it will be `"numpy"` when Numba is unavailable.

### `compile(...)` raises `ImportError`

`BM25.compile` always requires Numba. It is not a harmless no-op for a NumPy
retriever in a dependency-free environment. Skip compilation on the NumPy
fallback or install Numba before calling it.

### Explicit `csc_backend="scipy"` raises `ImportError`

Install SciPy or use `csc_backend="numpy"`/`"auto"`. With `"auto"`, inspect
`retriever.csc_backend` after construction; no later retry is performed.

### Explicit `backend_selection="jax"` raises `ImportError`

Install the CPU JAX selection extra, or select `"numpy"`. With
`backend_selection="auto"`, JAX availability is checked by `bm25s.selection`
and the selector falls back to NumPy.

### Numba is present but unusable

Numba can fail for reasons other than `ImportError` (for example an incompatible
binary dependency or an unsupported runtime). Treat that as an environment
failure, not as a proven fallback. Confirm a tiny `numba.njit` call and the
`bm25s.NUMBA_AVAILABLE` flag, then repair the environment before using
`backend="numba"`.

## Data and configuration failures

### Invalid CSC backend

Only `"numpy"`, `"scipy"`, and the constructor convenience value `"auto"` are
supported. An invalid value is rejected while building the index with a
`ValueError` whose message names the allowed `scipy`, `numpy` values. Fix the
configuration before changing dependencies.

### Invalid top-k backend

`bm25s.selection.topk` accepts `"numpy"`, `"jax"`, and `"auto"`; any other
value raises `ValueError` with `Invalid backend`. The Numba selector is a
different function and accepts only `backend="numba"`.

### `k` is larger than the corpus

`BM25.retrieve` rejects `k > num_docs` before calling a selector. Lower `k` or
index more documents. Do not rely on the lower-level selector to repair this:
NumPy top-k uses `argpartition`, and a too-large `k` is not a supported
retrieval configuration.

### Numba backend rejects the selector

When `retriever.backend == "numba"`, use
`retrieve(..., backend_selection="numba")` or leave it at `"auto"` so the
retrieval path rewrites it to Numba. Explicit `"numpy"` or `"jax"` is rejected
by the Numba functional path. To use those selectors, set
`retriever.backend = "numpy"` only when the index/retrieval state is otherwise
compatible, or construct a NumPy retriever deliberately.

### Empty or unknown queries look unlike the baseline

Acceleration does not repair tokenization or vocabulary mismatches. Compare
NumPy and Numba using the same token IDs and verify that unknown query terms
were removed or mapped by the tokenizer before retrieval. Route vocabulary,
empty-token, and query-shape questions to the tokenization/core routes.

## API and CLI failures

### Passing `backend_selection` to the wrong API

`backend` belongs to `BM25(...)`; `backend_selection` belongs to
`BM25.retrieve(...)` and the single-query selector. `csc_backend` belongs to
`BM25(...)` and affects index construction. Do not pass `backend_selection` to
`index` or expect the `bm25` CLI to expose these Python backend knobs.

### `sorted=False` differs between selectors

NumPy and Numba honor the unsorted request. The current JAX wrapper calls
`jax.lax.top_k` and returns its descending result regardless of the flag. If
ordering is part of an API contract, use `sorted=True` or the NumPy/Numba path
and compare document-score pairs rather than assuming backend-independent tie
ordering.

### Changing `retriever.backend` after construction

The public constructor performs dependency resolution once. Mutating the
attribute later can select a different retrieval branch without rebuilding or
recompiling the instance. Prefer a new `BM25` object for a backend comparison;
if a loaded object is intentionally switched, run the local correctness smoke
check first.

The repository CLI and high-level file search route do not provide a stable
acceleration flag contract here. Use the Python `BM25` API for backend choices;
route CLI parser questions to the high-level/CLI operating skill.

## Workflow-specific failures

### Numba is slower on the first request

This is expected JIT overhead. Call `compile(..., warmup=True)` during startup,
compile before `index` when CSC construction matters, and measure multiple
post-warmup requests. Keep the first-run cost visible in reports.

### `NUMBA_DISABLE_JIT` defeats an explicit warmup

The activation and warmup methods check this environment setting and return
without enabling the scorer when it is set. Unset it for Numba acceleration.
The constructor's auto-compile guard is also environment-sensitive in this
revision, so use explicit compile plus a smoke assertion rather than trusting
`auto_compile=True`.

### A Numba run changes thread behavior

The Numba functional path sets its thread count for the call and restores the
previous count. Use `n_threads=0` for one-thread local checks, `-1` only when
all CPUs are intentionally allowed, and a positive bounded value for controlled
measurements. `chunksize` is ignored by this path; a warning is expected when
it is supplied.

### A large or remote example fails

Do not diagnose acceleration with Hub/BEIR downloads, remote credentials, or
networked example scripts. Reproduce the backend choice using
[`scripts/numba_smoke.py`](../scripts/numba_smoke.py), then obtain explicit
approval for a separate large benchmark.
