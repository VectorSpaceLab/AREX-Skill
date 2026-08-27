# PyGAD installation and environment guide

## Core installation

Core PyGAD usage is lightweight:

```bash
python -m pip install pygad
```

Core imports require PyGAD plus its runtime dependencies (`numpy` and `cloudpickle`):

```python
import pygad
import numpy
print(pygad.__version__)
```

Use an isolated environment for experiments that install optional plotting or deep-learning frameworks.

## Optional extras

| Need | Install | Why |
| --- | --- | --- |
| Core GA, benchmarks, pure NumPy NN/CNN helpers | `python -m pip install pygad` | Installs core dependencies only. |
| Plot methods such as `plot_fitness()` and `plot_genes()` | `python -m pip install "pygad[visualize]"` | Adds `matplotlib`. |
| PDF reports via `GA.generate_report()` | `python -m pip install "pygad[report]"` | Adds `matplotlib` and `reportlab`. |
| Keras/Torch model adapters | `python -m pip install "pygad[deep_learning]"` | Adds `keras`, `tensorflow`, and `torch` according to package metadata. |

You can also install framework packages directly when the user's project already manages TensorFlow/Keras/PyTorch versions.

## Recommended import checks

```python
import pygad
print("pygad", pygad.__version__)

# Core modules.
import pygad.benchmarks
import pygad.gann
import pygad.cnn
import pygad.gacnn

# Optional modules; import only when needed.
try:
    import pygad.kerasga
except ModuleNotFoundError as exc:
    print("Keras adapter unavailable:", exc)

try:
    import pygad.torchga
except ModuleNotFoundError as exc:
    print("Torch adapter unavailable:", exc)
```

## Headless plotting setup

In scripts, notebooks running on servers, or CI, choose the Matplotlib backend before the first plot import/call:

```python
import matplotlib
matplotlib.use("Agg", force=True)
```

Then call PyGAD plot methods with `save_dir=...` and close returned figures when many plots are created.

## Version and API baseline

This skill was generated from PyGAD `3.7.0`. Important inspected public signatures include:

```python
pygad.GA(num_generations, num_parents_mating, fitness_func, ..., random_seed=None, logger=None)
pygad.load(filename)
pygad.GA.save(filename)
pygad.GA.generate_report(filename, title=None, sections=None, include_plots=None, figure_size_inches=(7.0, 4.5), notes=None, page_size="letter")
```

If a user's installed version differs substantially, check the local `pygad.__version__` and adapt parameter names before copying templates.

## Backend policy

- Required package backend for this skill: CPU-compatible Python environment.
- Optional framework backends: TensorFlow/Keras and PyTorch for `kerasga`/`torchga`.
- Optional accelerator backends: only relevant if the user's TensorFlow/PyTorch installation and model workload require CUDA, ROCm, MPS, or another accelerator.
- Do not treat a successful `import pygad` as proof that optional framework adapters are usable; import those modules directly when needed.

## Common environment choices

For reproducible local work:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install pygad
```

For report-capable experiments:

```bash
python -m pip install "pygad[report]"
```

For deep-learning adapter experiments, prefer the user's project-specific framework install instructions when they need GPU wheels or strict TensorFlow/PyTorch versions; then install PyGAD into that same environment.
