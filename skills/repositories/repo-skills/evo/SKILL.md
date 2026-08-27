---
name: evo
description: "Routes evo trajectory-evaluation workflows for APE/RPE, trajectory
  I/O, result analysis, configuration, and programmatic usage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# evo

Use this skill for the `evo` Python package, which evaluates odometry and SLAM trajectories, loads and converts trajectory files, compares saved results, manages package settings, and supports programmatic plotting and notebooks.

## Install

- Python: 3.10 or newer.
- Install from a checkout with `pip install -e .`.
- Install from PyPI with `pip install evo`.
- Optional extras only when you need them:
  - `pip install evo[rerun]` for Rerun workflows.
  - `pip install evo[gui]` for the Qt plot backend.
  - `pip install evo[geo]` for map tiles via `contextily`.

## Minimal checks

- Import check: `python -I -c "import evo; print(evo.__version__)"`
- Safe helper: `python scripts/check_env.py`
- CLI help: `evo --help`

## Route map

| User need | Go here |
| --- | --- |
| APE / RPE scoring, alignment, delta selection, result zips | [`sub-skills/metrics/SKILL.md`](sub-skills/metrics/SKILL.md) |
| Trajectory file formats, converters, sync, align, export, bag / MCAP loading | [`sub-skills/trajectory-data/SKILL.md`](sub-skills/trajectory-data/SKILL.md) |
| Saved result comparison, merge, table export, label cleanup | [`sub-skills/result-analysis/SKILL.md`](sub-skills/result-analysis/SKILL.md) |
| `evo_config`, `evo pkg`, `evo cat_log`, `evo_ipython` | [`sub-skills/configuration/SKILL.md`](sub-skills/configuration/SKILL.md) |
| Custom Python scripts, notebooks, plotting, Rerun, `contextily` | [`sub-skills/python-api/SKILL.md`](sub-skills/python-api/SKILL.md) |

## When to read the bundled references

- Read [`references/repo-provenance.md`](references/repo-provenance.md) when you need to know whether this skill still matches the current checkout.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import, optional dependency, backend, and settings problems.
- Run [`scripts/check_env.py`](scripts/check_env.py) when you want a quick import-and-CLI smoke check from an installed environment.

## Working rules

- Use the sub-skill that matches the user’s primary workflow instead of mixing APE/RPE, trajectory I/O, result comparison, and configuration into one answer.
- Treat trajectory and metric helpers as in-place mutators unless the reference says otherwise; copy inputs when you need to preserve originals.
- Keep references and scripts self-contained inside this skill tree. Do not rely on the original checkout being present.
- If the package or APIs change, compare the checkout against `references/repo-provenance.md` and refresh the skill when needed.
