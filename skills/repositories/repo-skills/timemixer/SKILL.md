---
name: timemixer
description: "Use TimeMixer to inspect the model API, build forecasting or
  non-forecast commands, validate dataset layouts, and debug shape or
  task-specific workflow issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TimeMixer

Use this repo skill for the TimeMixer time-series repository: model inspection, forecasting command construction, dataset layout validation, and the imputation/anomaly/classification branches.

## Start here

1. Install the runtime dependencies from `requirements.txt` in a Python environment that can import the source checkout.
   - The repository notes a Python 3.8 sktime compatibility pin (`sktime==0.29.1`) if you are reproducing the historical runtime exactly.
   - The repository is source-first rather than a packaged distribution, so the bundled helpers add the checkout to `sys.path` instead of depending on a wheel install.
2. Keep helper invocation and source execution roots distinct. The helper files live under the skill directory, while `run.py` and the source packages live at the checkout root. From any shell, use explicit absolute paths:

   ```bash
   CHECKOUT_ROOT=/path/to/TimeMixer-checkout
   SKILL_ROOT="$CHECKOUT_ROOT/skills/disco/timemixer"
   cd "$CHECKOUT_ROOT"
   python "$SKILL_ROOT/scripts/check_timemixer_environment.py" --repo-root "$CHECKOUT_ROOT"
   ```

   Generated `run.py` commands must likewise be executed with cwd `CHECKOUT_ROOT`; `--repo-root .` is only correct when the current directory is the source checkout, never when it is the skill directory.
3. Then route the task to the smallest matching sub-skill.

## Route map

| If the user asks for... | Use |
| --- | --- |
| Model construction, forward shapes, decomposition choices, downsampling, or classification shape debugging | `sub-skills/model-architecture/SKILL.md` |
| Forecasting benchmark commands, custom forecast adaptation, checkpoints, or M4/PEMS/ECL/Weather/Solar recipes | `sub-skills/forecasting-experiments/SKILL.md` |
| Dataset file layouts, CSV/NPY/TS validation, time-feature conventions, or benchmark data placement | `sub-skills/data-preparation/SKILL.md` |
| Imputation, anomaly detection, or classification workflows and task-specific command construction | `sub-skills/universal-tasks/SKILL.md` |

## Quick reference files

- Read `references/cli-reference.md` when you need the `run.py` argument groups or task-to-flag mapping.
- Read `references/troubleshooting.md` for install/import failures, the `run.py --help` percent-format bug, or other cross-cutting setup problems.
- Read `references/repo-provenance.md` when you need to check whether this skill matches a different TimeMixer checkout or before refreshing the skill.
- Read `references/repo-routing-metadata.json` only as managed-router metadata; it is not a user guide.

## Safe checks

- Use `scripts/check_timemixer_environment.py` to confirm that the checkout can be imported from a clean source-root path.
- Use `sub-skills/model-architecture/scripts/smoke_timemixer_forward.py` when you need a tiny CPU-only forward shape smoke.
- Use the forecasting or universal-task command builders before launching any long experiment.

## What this skill covers

- `TimeMixer.Model` architecture and forward behavior.
- Long-term and short-term forecast command construction.
- Custom dataset and benchmark data validation.
- Imputation, anomaly detection, and classification task branches.
- Common `run.py`, dataset, and tensor-shape failure modes.

## What it does not do

- It does not reproduce benchmark-scale training runs.
- It does not download datasets for you.
- It does not depend on the original source checkout being opened through the skill files themselves; the bundled references and scripts summarize the needed behavior.

## Notes for future agents

- `run.py --help` is unreliable because one help string contains an unescaped percent sign.
- Prefer the bundled command builders for safe command generation.
- Keep the root skill as a router; deeper API, workflow, and troubleshooting detail lives in the sub-skills.
