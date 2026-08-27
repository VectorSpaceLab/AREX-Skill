---
name: foundation-models-and-customization
description: "Navigate Time-Series-Library model files, optional Mamba and large
  time-series model dependencies, augmentation flags, and custom model or script
  additions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TSLib Models and Customization

Use this sub-skill when the task is about choosing a TSLib model, diagnosing optional model dependencies, using zero-shot foundation models or Mamba variants, adding a new `models/<Name>.py`, adapting benchmark scripts, or using the built-in augmentation flags.

## Route Here

- Explain how `Exp_Basic` discovers model files and how `--model <Name>` maps to `models/<Name>.py`.
- Choose a core smoke-test model versus an optional dependency-heavy model.
- Diagnose missing imports for `mamba_ssm`, `chronos`, `timesfm`, `uni2ts`, `tirex`, or `transformers`.
- Add or adapt a custom TSLib model file and create matching benchmark/smoke commands.
- Use augmentation flags such as `--jitter`, `--scaling`, `--permutation`, `--timewarp`, `--wdba`, or DTW-guided variants.
- Follow contribution expectations for new published-paper model additions.

## Reroute

- Forecast command construction, TimeXer recipes, or zero-shot task commands: use `../forecasting/SKILL.md`.
- Data layouts, `run.py` flag basics, GPU flags, and output folders: use `../data-and-cli/SKILL.md`.
- Imputation/anomaly/classification task-specific recipes: use `../imputation-anomaly-classification/SKILL.md`.

## Start Fast

Inventory safe core and optional model imports before recommending a model:

```bash
python scripts/inspect_tslib_models.py --repo-root . --models DLinear TimesNet TimeXer PatchTST --optional-models
```

For smoke tests, prefer `DLinear`, `TimesNet`, `TimeXer`, `PatchTST`, or `Transformer` before Mamba/LTSM files. Optional model import failures should be treated as routing information, not as a broken core TSLib install.

## Custom Model Contract

A model file normally lives at `models/<Name>.py` and exposes either `Model` or a class named `<Name>`. Most task models implement:

```python
class Model(nn.Module):
    def __init__(self, configs): ...
    def forward(self, x_enc, x_mark_enc, x_dec, x_mark_dec, mask=None): ...
```

`Exp_Basic` scans `models/` dynamically at runtime, so adding a Python file is enough for discovery if imports and the class contract are valid.

## References and Helpers

- `references/model-catalog-and-dependencies.md` maps model families to dependency and backend surfaces.
- `references/customization.md` covers custom model/script addition and augmentation usage.
- `references/troubleshooting.md` covers optional dependency, model import, shape, and source-tree problems.
- `scripts/inspect_tslib_models.py` probes model imports and class availability without downloading data or training.
- `../../references/model-catalog.md` is the shared catalog used by the root skill.

## Avoid

- Do not install all optional model stacks just because one import failed. First confirm the requested model family.
- Do not claim zero-shot, Mamba, or remote-code model execution is verified unless that exact package, model cache, and device path has been run.
- Do not add a model file without a small CPU-compatible shape/import smoke when possible.
- Do not copy upstream benchmark shell scripts without adjusting GPU ids, data paths, and epochs for the user's environment.
