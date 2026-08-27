# Install and startup runtime

This reference is for installing PySR, understanding what happens at import time, configuring JuliaCall before import, and deciding when a container or backend customization is appropriate.

## Install choices

| Situation | Recommended command | Notes |
| --- | --- | --- |
| Normal Python environment | `python -m pip install pysr` | Installs the Python package and base dependencies. Julia dependencies are resolved at first import. |
| Conda-first environment | `conda install -c conda-forge pysr` | Uses conda-forge packages; the JuliaCall package name may appear as `pyjuliacall` in conda environments. |
| Source checkout for development | `python -m pip install -e .` | Use only when editing PySR itself or testing a local backend customization. `setup.py` is intentionally not the install path. |
| Reproducible no-root runtime | Build and run a container image | Useful on clusters or locked-down hosts; still budget for first Julia package setup inside the image/container cache. |

Base Python dependencies include NumPy, pandas, SymPy, scikit-learn, JuliaCall, Click, and typing extensions. Optional extras such as JAX, PyTorch, TensorBoard, and autodiff Julia packages are not required for ordinary fitting/import readiness.

## What `import pysr` does

`import pysr` is not a lightweight pure-Python import. It immediately initializes JuliaCall, starts or locates a compatible Julia runtime, and loads the SymbolicRegression Julia backend. The packaged backend for this source snapshot is a 2.0 beta SymbolicRegression revision, with Julia constrained to a compatible 1.10 release line.

Expected first-use costs:

1. **Fresh Python environment:** package metadata is available quickly, but importing PySR can trigger Julia and Julia package resolution/download/precompilation.
2. **First import after setup:** JuliaCall starts Julia and PySR loads `using SymbolicRegression`.
3. **First `.fit()` in a process:** Julia JIT compilation can take noticeably longer than later fits in the same process.
4. **Subsequent fits in the same Python process:** usually much faster, because Julia and compiled code are already live.

Operational consequence: keep an IPython session, notebook kernel, worker process, or long-lived Python job alive while iterating. Repeatedly launching short scripts pays startup and compilation every time.

## Environment variables that must be set before import

Set these before any `import pysr` or `import juliacall`:

```bash
export PYTHON_JULIACALL_THREADS=auto      # or a fixed integer such as 8
export PYTHON_JULIACALL_HANDLE_SIGNALS=yes
export PYTHON_JULIACALL_OPTLEVEL=3
```

PySR sets these defaults itself only when JuliaCall has not already been imported. If JuliaCall is imported first, PySR warns that it cannot configure JuliaCall threads or optimization level for you.

Important details:

- Use `PYTHON_JULIACALL_THREADS`, not `JULIA_NUM_THREADS`, for PySR's JuliaCall startup path.
- Choose a fixed thread count for shared machines or CI; `auto` is convenient for single-user machines.
- If an IPython/Jupyter extension interaction causes Unicode or stdin-related issues, disable JuliaCall's IPython extension autoload before import with `PYTHON_JULIACALL_AUTOLOAD_IPYTHON_EXTENSION=no`.
- Do not change thread environment variables after import and expect the current process to change. Start a new Python process instead.

## Import order and library-linking failures

PySR imports its Julia bridge early to avoid common dynamic-library conflicts. If you see an import-time `GLIBCXX_... not found` failure, another package may have loaded an incompatible C++ runtime first. Practical fixes are:

1. Start a fresh process and import PySR before packages that load large compiled runtimes.
2. Prefer a clean environment from one package manager instead of mixing system, pip, and conda libraries.
3. If necessary, put the Julia runtime library directory first in `LD_LIBRARY_PATH`. Use your environment's Julia library directory; do not copy an absolute path from another machine.

## Noninteractive startup settings

Use `input_stream="devnull"` when the environment may not support PySR's stdin watcher:

```python
from pysr import PySRRegressor

model = PySRRegressor(
    niterations=100,
    timeout_in_seconds=600,
    input_stream="devnull",
)
```

This is especially useful for notebooks, CI jobs, background services, and schedulers. In terminal/IPython use, the default stdin stream lets you stop a search gracefully with `q` then Enter.

## Containers

Container use is operationally straightforward:

```bash
docker build -t pysr .
docker run -it --rm -v "$PWD:/work" -w /work pysr ipython
```

For clusters without Docker privileges, build an Apptainer image from a container definition and run the resulting image:

```bash
apptainer build --notest pysr.sif Apptainer.def
apptainer run pysr.sif
```

Container guidance:

- Build or warm the image/cache before many scheduled jobs when possible.
- Mount only the data/output directories needed by the run.
- Keep first-import Julia package setup inside a persistent image layer or persistent user cache if your cluster policy allows it.
- Do not bake credentials into the image.

## Backend customization

Most user needs should be solved with PySR options, custom operators, custom losses, constraints, template expressions, or export mappings. Route those design choices to `customization-and-constraints`. Edit the backend only when the Python options cannot represent the required algorithmic change.

A local SymbolicRegression backend workflow is:

1. Check out a SymbolicRegression.jl source tree matching the backend revision expected by the PySR package.
2. Modify the Julia backend.
3. In the PySR source tree, edit `pysr/juliapkg.json` so the `SymbolicRegression` package entry uses a local development path instead of a released revision.
4. Install PySR from that source tree with `python -m pip install -e .`.
5. Start a fresh Python process and run the environment probe plus a tiny fit before trusting long runs.

Keep backend path values out of reusable skill notes, logs, prompts, and examples; they are machine-local.

## Probe workflow

Use the bundled probe in escalating order:

```bash
python scripts/pysr_environment_probe.py --help
python scripts/pysr_environment_probe.py --skip-import --json
python scripts/pysr_environment_probe.py --json
python scripts/pysr_environment_probe.py --json --check-cli
```

The no-import probe is safe for quick triage. The import probe may perform first-time Julia setup. The CLI check is optional and time-bounded because `python -m pysr --help` imports the package.
