# Runtime and version checks

## Baseline import check

```bash
python - <<'PY'
import fairlearn
print(fairlearn.__version__)
from fairlearn.metrics import MetricFrame
from fairlearn.preprocessing import CorrelationRemover
from fairlearn.postprocessing import ThresholdOptimizer
from fairlearn.reductions import ExponentiatedGradient, GridSearch, DemographicParity
from fairlearn.adversarial import AdversarialFairnessClassifier
from fairlearn.datasets import fetch_adult
print('fairlearn imports OK')
PY
```

## Root bundled check

From the generated Fairlearn skill directory:

```bash
python scripts/check_install.py --include-optional
```

From the installation sub-skill directory route:

```bash
python sub-skills/installation/scripts/check_runtime.py --include-optional
```

`--include-optional` imports optional modules when present and reports missing optional modules without failing the core package check.

## Workflow-specific probes

| Workflow | Probe |
| --- | --- |
| Assessment metrics | `python sub-skills/assessment/scripts/smoke_assessment.py` |
| Assessment plots | `python sub-skills/assessment/scripts/smoke_assessment.py --plot` |
| Preprocessing | `python sub-skills/preprocessing/scripts/smoke_preprocessing.py` |
| Reductions | `python sub-skills/reductions/scripts/smoke_reductions.py` |
| Postprocessing | `python sub-skills/postprocessing/scripts/smoke_threshold_optimizer.py` |
| Postprocessing plots | `python sub-skills/postprocessing/scripts/smoke_threshold_optimizer.py --plot` |
| PyTorch adversarial | `python sub-skills/adversarial/scripts/smoke_torch_adversarial.py` |
| Optional CUDA adversarial | `python sub-skills/adversarial/scripts/smoke_torch_adversarial.py --cuda cuda:0` |
| Dataset signatures without network | `python sub-skills/datasets/scripts/preview_dataset_loaders.py` |

Run only the probes needed for the user's selected workflow.

## `show_versions()`

```python
import fairlearn
fairlearn.show_versions()
```

The function prints system and package metadata including Python, executable, machine, Fairlearn, pip, setuptools, numpy, scipy, Cython, pandas, matplotlib, sklearn, lightgbm, pytorch, and tensorflow. It may report `None` for a dependency if package metadata cannot be found under the expected distribution name. When in doubt, verify direct imports separately.

## Optional dependency install recovery

```bash
python -m pip install matplotlib
python -m pip install torch
python -m pip install tensorflow
```

Install only the dependency needed by the current task. Do not install all optional ML stacks just because the root check reports them missing.

## Staleness checks

Compare a future checkout/release with `../../references/repo-provenance.md` if:

- constructor signatures changed;
- optional extra names changed;
- Python minimum changed;
- public exports were renamed or removed;
- dataset loaders changed schema or cache behavior;
- adversarial backend errors differ from this skill.
