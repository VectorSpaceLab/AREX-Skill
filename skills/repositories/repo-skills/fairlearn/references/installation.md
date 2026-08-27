# Fairlearn installation and runtime checks

Fairlearn is a Python package with sklearn-style APIs and no Fairlearn-specific CLI in this checkout.

## Supported baseline

- Package name: `fairlearn`.
- Python requirement in the inspected source: `>=3.11`.
- Core dependencies in the inspected source: `narwhals`, `numpy`, `pandas`, `scikit-learn`, and `scipy`.
- Observed source package version during construction: `0.15.0.dev0`.

## Install commands

For released package use:

```bash
python -m pip install fairlearn
```

For conda-forge environments:

```bash
conda install -c conda-forge fairlearn
```

For a local checkout when the user is editing the repository:

```bash
python -m pip install -e .
```

Do not install broad development requirements unless the user is maintaining the repository or running the repo's own tests. Runtime package-user workflows only need the core package plus optional dependencies selected by the task.

## Optional dependencies by workflow

| Workflow | Dependency | How to verify | Notes |
| --- | --- | --- | --- |
| Assessment and postprocessing plots | `matplotlib` | `python -c "import matplotlib"` | The user guide names a plotting extra, while the runtime error string may mention `fairlearn[customplots]`; direct `python -m pip install matplotlib` is the safest recovery. |
| Adversarial mitigation with PyTorch | `torch` | `python -c "import torch; print(torch.__version__)"` | PyTorch CPU and optional CUDA were verified in this skill run. |
| Adversarial mitigation with TensorFlow | `tensorflow` / `keras` | `python -c "import tensorflow"` | Source supports TensorFlow as an alternative backend, but this skill run did not verify it. |
| Built-in datasets | network/cache access to OpenML-style sources | try a single loader with explicit `data_home` | Dataset fetchers can download data; use cached data or a chosen data-home in restricted environments. |

## Quick import check

From this skill directory:

```bash
python scripts/check_install.py --include-optional
```

The script checks stable public submodule imports and reports optional dependencies without failing when optional dependencies are absent.

For a raw Python check:

```python
import fairlearn
print(fairlearn.__version__)
from fairlearn.metrics import MetricFrame, selection_rate
from fairlearn.preprocessing import CorrelationRemover, PrototypeRepresentationLearner
from fairlearn.postprocessing import ThresholdOptimizer
from fairlearn.reductions import ExponentiatedGradient, GridSearch, DemographicParity
from fairlearn.adversarial import AdversarialFairnessClassifier
```

## Version diagnostics

Fairlearn exposes `show_versions()` at the top level:

```python
import fairlearn
fairlearn.show_versions()
```

`show_versions()` prints system, Python, and dependency information. Use it for debugging local installs, but do not paste private local paths into public reports unless the user asks for environment diagnostics.

## When to switch sub-skills

- Imports succeed and the task is about grouped metrics or plots: use `sub-skills/assessment/`.
- Imports succeed and the task is about a mitigation algorithm: use the relevant mitigation sub-skill.
- The failure mentions matplotlib or plotting: read root troubleshooting and the plotting-owning sub-skill.
- The failure says to install `torch`, `tensorflow`, or `torch or tensorflow`: read `sub-skills/adversarial/` and check backend availability.
- The failure is a network/cache problem from a dataset fetcher: read `sub-skills/datasets/`.
