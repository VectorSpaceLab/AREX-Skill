# Cross-Cutting Troubleshooting

Use this reference for package-level failures that are broader than one
sub-skill. For workflow-specific errors, follow the nearest sub-skill's
troubleshooting reference.

## Install or import fails

Symptoms:

```text
ModuleNotFoundError: No module named 'bayes_opt'
PackageNotFoundError: bayesian-optimization
ImportError involving numpy, scipy, sklearn, packaging, or colorama
```

Likely causes:

- The distribution was not installed in the active Python environment.
- The user installed a different package name or is using a stale environment.
- Dependency markers selected incompatible NumPy/SciPy/scikit-learn versions for
  the active Python.
- A source checkout is being tested from one Python while another Python is used
  for imports.

Recovery:

```bash
python -m pip install bayesian-optimization
python - <<'PY'
from importlib.metadata import version
import bayes_opt
print('distribution', version('bayesian-optimization'))
print('module', bayes_opt.__version__)
PY
```

If maintaining a checkout, use the maintainer sub-skill and verify the checkout
import path with its development workflow guidance.

## Python and dependency marker mismatch

The package supports Python `>=3.9` and uses version markers for newer Python
releases. Practical compatibility rules distilled from package metadata and CI:

- Python `<3.13`: NumPy `>=1.25` is supported.
- Python `>=3.13,<3.14`: NumPy `>=2.1.3`, SciPy `>=1.14.1`.
- Python `>=3.14`: NumPy `>=2.3.0`, SciPy `>=1.17.0`, scikit-learn `>=1.8.0`,
  packaging `>=26.0`.
- CI excludes NumPy 1 on Python 3.13 and newer.

If a resolver tries to combine Python 3.13+ with NumPy 1, treat the environment
as wrong. Use a supported Python/NumPy lane instead of overriding the markers.

## No package CLI exists

Symptoms:

- The user asks for a `bayesian-optimization` command-line invocation.
- `python -m bayes_opt` or a guessed shell command fails.

Recovery:

This package exposes Python APIs rather than a user CLI. Route to:

- optimizer construction and HPO: `sub-skills/optimizer-workflows/SKILL.md`;
- acquisition controls: `sub-skills/acquisition-control/SKILL.md`;
- constraints/typed domains/domain reduction: `sub-skills/advanced-domain-features/SKILL.md`.

Use bundled scripts as diagnostics or examples after package installation; they
are skill helpers, not upstream package commands.

## Old `UtilityFunction` examples or stale `suggest(util)` code

Symptoms:

```python
from bayes_opt.util import UtilityFunction
optimizer.suggest(utility)
```

Current v3.3.x behavior:

- `bayes_opt.util` exports random-state utilities, not a public
  `UtilityFunction` class.
- `BayesianOptimization.suggest()` takes no acquisition argument.
- Acquisition functions are objects from `bayes_opt.acquisition` passed to the
  `BayesianOptimization(..., acquisition_function=...)` constructor.

Recovery:

```python
from bayes_opt import BayesianOptimization, acquisition

optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-2.0, 2.0)},
    acquisition_function=acquisition.UpperConfidenceBound(kappa=2.576),
    random_state=1,
)
params = optimizer.suggest()
```

For async or batch-like patterns, use the acquisition-control sub-skill's
Constant Liar guidance.

## Objective returns invalid values

Symptoms:

- scikit-learn or SciPy errors during GP fit;
- `nan` or `inf` targets;
- no meaningful `optimizer.max`.

Likely causes:

- The objective raised for some legal point and returned a non-finite fallback.
- A loss was returned with the wrong sign.
- The target wrapper returns arrays/tensors instead of a scalar float.
- Bounds include invalid model configurations.

Recovery:

1. Run a tiny budget first.
2. Validate the objective manually at random samples.
3. Convert targets to finite Python floats.
4. Return `-loss` for losses.
5. Narrow bounds or catch invalid model configurations with a low finite score.

## Wrong route selected

Use the root route map:

- Ordinary package usage, HPO, state, predictions, `pbounds`, and ask-tell:
  `sub-skills/optimizer-workflows/SKILL.md`.
- Acquisition choice/tuning/customization/async: `sub-skills/acquisition-control/SKILL.md`.
- Constraints, typed parameters, `TargetSpace`, and domain reduction:
  `sub-skills/advanced-domain-features/SKILL.md`.
- Editing the source repository and choosing native tests/docs/lint:
  `sub-skills/repo-maintenance/SKILL.md`.

When a task spans multiple areas, start with the domain or optimizer route that
owns the user's desired output, then cross-link only for the specialized detail.

## GPU or accelerator confusion

The selected workflows for this package are CPU scientific Python workflows.
NumPy, SciPy, and scikit-learn are the relevant runtime dependencies; a visible
CUDA/ROCm/MPS device is not required for package use or verification. Do not
install GPU frameworks solely because hardware is present.

## Running bundled diagnostics

From the generated skill tree after installing the package:

```bash
python scripts/check_env.py
python scripts/check_env.py --run-subskill-smokes
```

Or run sub-skill helpers directly when investigating a specific route:

```bash
python sub-skills/optimizer-workflows/scripts/bo_core_smoke.py
python sub-skills/acquisition-control/scripts/acquisition_probe.py --include-constant-liar
python sub-skills/advanced-domain-features/scripts/advanced_features_smoke.py --check all
python sub-skills/repo-maintenance/scripts/select_native_checks.py bayes_opt/acquisition.py
```

The diagnostics use small synthetic problems, no network, and no destructive
writes by default. The maintainer helper prints commands only; it does not run
native tests.
