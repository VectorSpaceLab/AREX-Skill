# Cross-cutting troubleshooting

## Read this when

Use this page when installation, import, or package-wide smoke checks fail before you have narrowed the issue to a specific geometry sub-skill.

## Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: ensemble_boxes` | The package is not installed in the active environment, or the wrong Python is being used. | Install `ensemble-boxes` in the target environment, then re-run `python -c "from ensemble_boxes import weighted_boxes_fusion"`. Use `python -m pip check` to catch dependency conflicts. |
| `ImportError` from `numpy`, `pandas`, or `numba` | A version mismatch or broken wheel install. | Reinstall the package set in one environment, then run the root smoke helper again. The package requires NumPy, Pandas, and Numba at runtime. |
| The root smoke helper prints GUI-related errors | You tried to use a visualization path that needs OpenCV or Matplotlib with a display server. | Prefer the bundled non-GUI smoke scripts. Install OpenCV/Matplotlib only if you intentionally need interactive plotting. |
| Benchmark scripts fail with missing `pycocotools` or `map_boxes` | Benchmark-only dependencies are optional and were not installed. | Read `references/benchmark-notes.md`. Install the extra packages only when you explicitly want to reproduce the benchmark workflows. |
| Benchmark scripts fail because data files are missing | The benchmark scripts depend on external CSV/JSON files that are not bundled with the package. | Treat benchmark execution as an optional data-download workflow. Use the benchmark notes to identify the expected files and skip the benchmark if you do not have them. |
| `Unknown conf_type` or `SystemExit` appears while checking a geometry helper | The chosen confidence mode is not supported by that API path. | Check the relevant sub-skill reference for the accepted values and retry with one of the documented modes. |
| The root smoke helper passes, but one geometry-specific task still fails | The problem is probably in the 2D, 1D, or 3D input contract rather than in the package installation itself. | Route to the matching sub-skill troubleshooting page and inspect the geometry-specific coordinate, label, or confidence-mode rules. |

## First recovery steps

1. Verify the active Python and `ensemble_boxes` import.
2. Run `python -m pip check` in the same environment.
3. Run `python scripts/check_install.py --case all`.
4. If the root smoke passes, move to the matching sub-skill for geometry-specific debugging.

## When to stop

Stop and repair the environment if the package cannot be imported or if `pip check` fails. Do not try to debug geometry until the environment is known-good.
