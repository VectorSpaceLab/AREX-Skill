# MedMNIST API overview

Read this when choosing a public object or checking that an environment is
complete. Facts below are based on the package source and a live inspection of
release 3.0.2.

## Object map

- `medmnist.INFO` is the registry for 18 subsets. Each record provides
  `python_class`, task, label meanings, channel count, split sample counts,
  official Zenodo URLs/checksums, and license.
- `medmnist.MedMNIST` is the shared dataset base. Its verified constructor is
  `MedMNIST(split, transform=None, target_transform=None, download=False,
  as_rgb=False, root="~/.medmnist", size=None, mmap_mode=None)`.
- `MedMNIST2D` subclasses expose 2D classes such as `PathMNIST`, `ChestMNIST`,
  `PneumoniaMNIST`, and `OrganAMNIST`; 2D sizes are 28, 64, 128, and 224.
  Items are Pillow images plus integer NumPy target arrays.
- `MedMNIST3D` subclasses expose `OrganMNIST3D`, `NoduleMNIST3D`,
  `AdrenalMNIST3D`, `FractureMNIST3D`, `VesselMNIST3D`, and `SynapseMNIST3D`;
  3D sizes are 28 and 64. Items are normalized channel-first NumPy arrays
  with one or three channels plus integer targets.
- `medmnist.Evaluator` has the verified constructor
  `Evaluator(flag, split, size=None, root="~/.medmnist")`. It reads labels from
  the matching NPZ and returns `Metrics(AUC, ACC)` from `evaluate()`.
- `python -m medmnist` is a Fire CLI. Public commands are `available`,
  `download`, `clean`, `info`, `save`, `evaluate`, and a development-only
  `test`. Only `available` and `info` are read-only metadata commands by
  default.

## Minimal import diagnostic

```python
import medmnist
from medmnist import INFO, PathMNIST, Evaluator

print(medmnist.__version__, len(INFO))
print(PathMNIST, Evaluator)
```

If this fails before any dataset is constructed, repair the package dependency
set first. If construction fails, check the root and exact NPZ filename in the
focused loading or evaluation route rather than reinstalling blindly.

## Task and shape decision

Read `INFO[flag]["task"]` before generating scores or labels. The task values in
this release are `binary-class`, `multi-class`, `multi-label, binary-class`, and
`ordinal-regression`. Label arrays are stored as `(N, L)` even for single-label
subsets. Evaluation score shapes and thresholds are documented in the
[evaluation API reference](../sub-skills/evaluation-and-export/references/api-reference.md).
