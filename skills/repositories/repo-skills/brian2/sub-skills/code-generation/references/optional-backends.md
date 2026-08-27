# Optional native backends: GSL

GNU Scientific Library (GSL) support is optional. Core Brian2 runtime and C++
standalone workflows do not require GSL unless a model selects a GSL state
updater or directly uses GSL-dependent generated code.

## What GSL adds

Brian2 exposes GSL adaptive/integration state-updater variants including
`gsl_rk2`, `gsl_rk4`, `gsl_rkf45`, `gsl_rkck`, and `gsl_rk8pd` (the short
`method="gsl"` spelling selects the GSL default path). GSL is an experimental
or specialized numerical route: it has method options for adaptive timestep,
absolute error, maximum steps, reuse of the last timestep, failed-step
recording, and step-count recording. Those options change numerical behavior
and should be selected from the model's accuracy requirements, not merely to
obtain a compiler target.

GSL is separate from Cython. Runtime GSL supports the runtime device only with
Cython code generation; NumPy runtime GSL is not implemented. C++ standalone
has a dedicated GSL code object and links the GSL and GSL CBLAS libraries.

## Prerequisites

A working GSL installation needs both development headers and linkable
libraries (the package documentation describes GSL >= 1.16). Brian2's
`prefs.GSL.directory` is either `None` when headers are already on the active
compiler's include path, or a directory whose `gsl/` subdirectory contains at
least `gsl_odeiv2.h`, `gsl_errno.h`, and `gsl_matrix.h`. The standalone path
also needs the `gsl` and `gslcblas` libraries and a runtime loader path where
applicable.

```python
from brian2 import prefs
prefs.GSL.directory = "/path/to/gsl/include-prefix"
```

Brian2 validates the configured directory; a nonexistent path or missing
required header is a preference error. On Windows, the corresponding runtime
DLL location must also be discoverable. Prefer the package/environment's
normal include and library paths over hard-coded machine-specific settings.

Do not treat a Python `import brian2` or a Cython availability probe as GSL
validation. A tiny GSL model must compile and run in the intended target to
claim GSL support.

## Failure and fallback

Typical symptoms of missing GSL are an import/link/compile error naming
`gsl_odeiv2.h`, `gsl_errno.h`, `gsl_matrix.h`, `gsl`, or `gslcblas`, or a runtime
loader error for a GSL shared library. Check headers, libraries, compiler
search paths, and loader paths in the same environment; do not silently change
the model's method and claim equivalent output.

If GSL is absent, use a supported non-GSL updater such as `exact`,
`exponential_euler`, or `euler` when appropriate for the equations. This is a
functional fallback only: it can have different stability, adaptive-step,
accuracy, and stochastic behavior. GSL's state updater explicitly rejects
stochastic equations, so a stochastic model needs a non-GSL method even when
GSL is installed. GSL integration is experimental and its generator also has
narrower equation/code restrictions than the general runtime path; treat a
successful ordinary runtime or NumPy run as no evidence that GSL will compile.

GSL tests and comparisons are optional verification. Keep them skipped when the
system library is absent, and report the dependency gap. Do not install or
fetch a system library as part of an ordinary tiny smoke.
