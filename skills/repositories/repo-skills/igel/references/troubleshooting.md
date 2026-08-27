# Igel cross-cutting troubleshooting

Use this file for install/import problems that affect the whole package, not for workflow-specific errors. Tabular workflow failures live in [tabular-workflows](../sub-skills/tabular-workflows/SKILL.md), serving failures live in [deployment](../sub-skills/deployment/SKILL.md), and AutoKeras issues live in [auto-ml](../sub-skills/auto-ml/SKILL.md).

## Legacy install/import stack

Igel 0.7.0 is a legacy package version. The verified environment needed a Python 3.8-era dependency stack and had to avoid modern resolver behavior that rejects old metadata.

### Common symptoms

- `pip` refuses to install or resolve `uvicorn 0.14.0` metadata.
- `AttributeError: module 'numpy' has no attribute 'float'` during import.
- `ImportError: cannot import name 'pinv2' from scipy.linalg` during import or CLI startup.
- `igel` imports successfully in one environment but fails after dependency drift in another.

### Recovery path

1. Use a clean Python 3.8-compatible environment for this package version.
2. Reinstall the legacy-compatible NumPy/SciPy/scikit-learn stack together instead of upgrading only one package.
3. Re-run the smoke checker:

```bash
python scripts/check_env.py
```

4. Confirm the CLI and import surface with `igel --help`, `igel models`, and `igel metrics`.

## When to stop and reroute

- If the task is really about tabular config/data/model selection, route to [tabular-workflows](../sub-skills/tabular-workflows/SKILL.md).
- If the task is about serving or HTTP prediction, route to [deployment](../sub-skills/deployment/SKILL.md).
- If the task is about AutoKeras task selection or `IgelCNN`, route to [auto-ml](../sub-skills/auto-ml/SKILL.md).

## Public notes that are safe to remember

- The current docs and source are slightly out of sync for some old examples, especially `auto-train`.
- `gui` and the source Dockerfile are not verified self-contained runtime paths for this skill set.
- ONNX export, serving, and Auto-ML all depend on the legacy environment being importable first; if import is broken, fix the environment before chasing workflow bugs.
