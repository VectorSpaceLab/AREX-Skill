# AB3DMOT cross-cutting troubleshooting

Use this root troubleshooting page when the failure is not yet clearly owned by data conversion, tracking, or evaluation. Once the failing workflow is known, switch to the nearest sub-skill troubleshooting page.

## `ModuleNotFoundError: AB3DMOT_libs`

Repository commands must run with an AB3DMOT checkout root on `PYTHONPATH`;
the generated skill directory is not the checkout and must not be substituted
as the command cwd. For direct checkout commands:

```bash
cd /path/to/AB3DMOT
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python main.py --help
```

For the generated smoke/checker helpers, do not rely on cwd: pass
`--repo-root /path/to/AB3DMOT` (and `--toolbox-root` when needed).

## `ModuleNotFoundError: xinshuo_io` or `xinshuo_miscellaneous`

The documented Xinshuo Python toolbox dependency is missing from the runtime
import path. Xinshuo is an external checkout, not a bundled sample or a
fixed dependency in this skill.

Recovery:

1. Clone/install Xinshuo_PyToolbox following its own instructions.
2. Add its root to `PYTHONPATH`, or pass it explicitly to the generated helper.
3. Re-run from the generated skill directory:
   ```bash
   python scripts/ab3dmot_environment_check.py \
     --repo-root /path/to/AB3DMOT \
     --toolbox-root /path/to/Xinshuo_PyToolbox
   ```

Do not remove toolbox imports from AB3DMOT unless you are intentionally patching the repository and can re-verify all workflows.

## Dependency pins fail on modern Python

The docs target Python 3.6 and older packages. On modern hosts, exact pins such as older scikit-learn, numba, matplotlib, OpenCV, or PyYAML may not install cleanly.

Recovery:

- Prefer a compatible Python environment when reproducing historical results.
- If a newer Python is required, install compatible newer versions and verify with `main.py --help`, conversion/evaluation `--help`, and the bundled synthetic smoke.
- Record any version drift before comparing benchmark numbers.

## Detections exist but full tracking cannot start

Detection folders are not full datasets. Full command-level tracking also needs calibration, ego-motion, and image frame lists under the dataset-specific tracking root.

Route to [sub-skills/data-conversion/references/troubleshooting.md](../sub-skills/data-conversion/references/troubleshooting.md) for dataset-layout recovery.

## `main.py` ran the wrong dataset

The parser default is `--dataset nuScenes`; the README quick demo uses KITTI only because it passes `--dataset KITTI`. Always build explicit commands.

Route to [sub-skills/tracking-pipeline/references/configuration.md](../sub-skills/tracking-pipeline/references/configuration.md) and the tracking command builder.

## Evaluation cannot find result folders

Evaluation and visualization are downstream of `main.py` result generation. Check whether the result SHA is combined (`<det>_<split>_H1`) or category-specific (`<det>_<category>_<split>_H1`), whether confidence thresholding added `_thres`, and whether `data_0`/`trk_withid_0` exist.

Route to [sub-skills/evaluation-visualization/references/result-layout.md](../sub-skills/evaluation-visualization/references/result-layout.md).

## Server metrics are requested for a test set

KITTI and nuScenes test labels are not locally available. A local command can package or convert submission artifacts, but official test metrics require external benchmark servers.

Do not promise local test metrics. Provide the submission artifact path and note the external evaluation step.

## Warnings during import or help checks

Known non-fatal warnings include:

- `SyntaxWarning` for `is`/`is not` string comparisons.
- Numba deprecation warnings for `@jit` object-mode defaults.

If the command exits 0 and smoke checks pass, record the warnings but continue. If a future runtime turns warnings into errors, use a compatible Python or patch the repository and re-run focused checks.
