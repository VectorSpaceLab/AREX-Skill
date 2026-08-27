# Repo provenance

- Schema: `disco.repo-provenance.v1`

## Source baseline

- Repository: PyGAD / GeneticAlgorithmPython
- Public remote: `https://github.com/ahmedfgad/GeneticAlgorithmPython.git`
- Commit: `703461dfc66966f0089567e82a7b9518732ad5dc`
- Branch: `master`
- Exact tag: none found for this checkout
- Package distribution/import name: `pygad`
- Package version: `3.7.0`
- Skill id: `pygad`

## Working tree state at generation time

The checkout was dirty because the `skills/` production output directory was untracked. No source package files were intentionally modified for this skill. The environment preparation step briefly created build metadata during editable installation; that metadata was removed before final skill verification.

## Evidence paths used

- `README.md`
- `pyproject.toml`
- `setup.py`
- `requirements.txt`
- `docs/requirements.txt`
- `docs/source/index.md`
- `docs/source/pygad.md`
- `docs/source/steps_to_use.md`
- `docs/source/fitness_calculation.md`
- `docs/source/gene_values.md`
- `docs/source/adaptive_mutation.md`
- `docs/source/multi_objective.md`
- `docs/source/user_defined_operators.md`
- `docs/source/benchmarks.md`
- `docs/source/visualize.md`
- `docs/source/logging.md`
- `docs/source/nn.md`
- `docs/source/gann.md`
- `docs/source/cnn.md`
- `docs/source/gacnn.md`
- `docs/source/kerasga.md`
- `docs/source/torchga.md`
- `pygad/pygad.py`
- `pygad/utils/validation.py`
- `pygad/utils/engine.py`
- `pygad/utils/parent_selection.py`
- `pygad/utils/crossover.py`
- `pygad/utils/mutation.py`
- `pygad/utils/nsga.py`
- `pygad/utils/nsga2.py`
- `pygad/utils/nsga3.py`
- `pygad/utils/quality_indicators.py`
- `pygad/utils/report.py`
- `pygad/visualize/plot.py`
- `pygad/benchmarks/`
- `pygad/nn/`, `pygad/gann/`, `pygad/cnn/`, `pygad/gacnn/`, `pygad/kerasga/`, `pygad/torchga/`
- Representative files under `examples/`
- Representative behavior tests under `tests/`

## Verification baseline

Core package, benchmark, visualization/report, and pure NumPy neural helper checks were verified against a private CPU inspection environment. Keras/Torch adapter signatures and templates are included, but full optional framework native verification is conditional on installing TensorFlow/Keras/PyTorch in the user's runtime environment.

## Refresh triggers

Refresh this skill when any of these change materially:

- `pygad.GA` constructor parameters, callback signatures, or validation behavior.
- Multi-objective selector behavior, NSGA-III reference-point handling, or quality indicator semantics.
- Plot method preconditions or report generation dependencies.
- Benchmark class names, fitness sign convention, constructor defaults, or `pareto_front()` support.
- `pygad.nn`, `gann`, `cnn`, `gacnn`, `kerasga`, or `torchga` weight-conversion contracts.
- Package extras in `pyproject.toml`.
