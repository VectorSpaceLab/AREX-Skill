# Package Renaming Checklist

Lightning-Hydra-Template starts with distribution/import package `src`. Many derived projects rename it. Rename carefully because config targets, tests, entry points, and CI all depend on the package name.

## Update together

| Area | What to update |
| --- | --- |
| Source tree | Rename `src/` package directory or create the new package; update `__init__.py` and imports. |
| Entry points | In `setup.py`, change `train_command = src.train:main` and `eval_command = src.eval:main` to the new package paths. |
| Distribution name | Optionally change `setup(name="src")` to the project distribution name. |
| Hydra configs | Update every `_target_: src....` in `configs/data`, `configs/model`, and any custom configs. |
| Tests | Update imports from `src.train`, `src.eval`, datamodules, model modules, and helper paths. |
| Coverage | Change CI command `pytest --cov src` to the new import package. |
| Docs/Makefile | Update any commands if entry files move; `python src/train.py` may become `python newpkg/train.py` or console scripts only. |
| Root setup | Keep `.project-root` or update `rootutils.setup_root(..., indicator=...)` and `configs/paths/default.yaml`. |

## Verification sequence

```bash
pip install -e .
python - <<'PY'
from importlib.metadata import entry_points
print([ep for ep in entry_points(group='console_scripts') if ep.name in {'train_command', 'eval_command'}])
PY
python <this-skill>/sub-skills/customize-data-model/scripts/check_hydra_targets.py --repo-root .
pytest tests/test_configs.py -q
```

If imports pass but console scripts still point to `src.*`, reinstall editable after changing `setup.py`.

## Common partial-rename failures

- Config composition succeeds until instantiation, then fails on stale `_target_` paths.
- Tests import the old package while source moved to the new package.
- CI coverage uploads no useful data because `--cov src` no longer matches.
- `train_command --help` imports the old module path from stale editable metadata.
- Rootutils finds the wrong root after moving entry files without keeping `.project-root`.
