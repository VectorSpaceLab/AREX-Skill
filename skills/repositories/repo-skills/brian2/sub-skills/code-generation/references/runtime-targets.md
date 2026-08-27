# Runtime targets, Cython, and NumPy

## Target decision

Brian2's runtime device stores arrays in memory and runs the network loop from
Python. Code objects for numerical integration, synaptic propagation, and
similar work use the selected target. `prefs.codegen.target` accepts:

- `"auto"` (default): choose Cython if its availability probe can compile a
  tiny extension; otherwise choose NumPy and emit a one-time fallback message.
- `"cython"`: generate C++ through Cython and compile extension modules. This
  is a performance target, not a pure-Python mode.
- `"numpy"`: use the broadly portable Python/NumPy implementation. It does
  not need a C compiler and is the recovery target when native compilation is
  unavailable.
- A compatible `CodeObject` class for advanced extensions; do not invent one
  for an ordinary user request.

The target is distinct from the device. `prefs.codegen.target = "cython"`
selects runtime Cython code objects; it does not select C++ standalone. Use
`set_device("cpp_standalone")` for a generated standalone project.

A useful explicit fallback is:

```python
from brian2 import prefs
prefs.codegen.target = "numpy"
```

Set it before constructing the model. If a Cython or standalone compile failed,
this preserves ordinary runtime functionality but does not reproduce the
performance, native binary, or standalone constraints of the failed path.
Record that limitation rather than reporting a full native recovery.

## Cython prerequisites and behavior

The Cython target needs all of the following in the active package environment:

1. Brian2's installed compiled support extensions must be importable.
2. The Cython package must import.
3. A usable C/C++ compiler and Python build headers/toolchain must be visible.
4. The compiler must accept Brian2's generated C++ and the configured include,
   library, and compile flags.

The availability probe itself compiles and calls a tiny Cython extension, and
Brian caches the result of the `auto` choice for the process. It is a useful
preflight but does not guarantee every model's generated code will compile.
A model can still fail later due to an unsupported expression, user function,
compiler flag, or external library. The final model's first execution remains
the real validation.

The first runtime Cython use can be slower because it generates and compiles a
module. Brian2 hashes relevant code and environment inputs and keeps compiled
extensions in a cache, so compatible later uses can load them without a full
recompile. The cache key accounts for the generated code, Python
executable/version, Cython and NumPy major/minor versions, and `CC`/`CXX`
choices; changing those can legitimately create another extension.

Relevant preferences are:

```python
prefs.codegen.runtime.cython.cache_dir = "/writable/cache"
prefs.codegen.runtime.cython.multiprocess_safe = True
prefs.codegen.runtime.cython.delete_source_files = True
prefs.codegen.max_cache_dir_size = 1000  # MB warning threshold; 0 disables warning
```

`cache_dir=None` uses Cython's cache location with a Brian extensions
subdirectory. Set an explicit writable directory when the default is on a
read-only, quota-limited, or network filesystem. Keeping generated `.pyx`/C++
sources (`delete_source_files=False`) is useful for diagnosis but consumes
space. The cache is not a model results directory.

Use `clear_cache("cython")` only when stale or incompatible extensions need to
be removed and the cache contents are no longer needed. Do not delete arbitrary
cache directories while another process may compile into them. On a shared
filesystem keep the multiprocess-safe lock enabled; concurrent network-filesystem
runs can still be fragile, so prefer a local cache for verification.

## Diagnosis order

When `auto` falls back unexpectedly, first inspect the warning and run an
explicit NumPy tiny runtime case. Then test Cython availability in the same
environment, inspect the compiler executable and `CC`/`CXX`, and try a local
writable cache. If Cython is unavailable, do not force it repeatedly: use NumPy
for a functional result and report the native prerequisite gap. If a specific
model fails under Cython, compare it with NumPy to separate model/API errors
from compiler/code-generation errors.

Do not confuse a successful Python import, a Cython availability probe, and a
successful standalone native build. They are three different checks.
