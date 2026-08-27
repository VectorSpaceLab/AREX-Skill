# Norfair cross-cutting troubleshooting

Use this page when the problem is about installing, importing, or routing the right Norfair extra. For tracker lifecycle, distance, and ReID behavior, route to [`sub-skills/tracking-core/SKILL.md`](../sub-skills/tracking-core/SKILL.md). For OpenCV video drawing or camera motion, route to [`sub-skills/video-visualization/SKILL.md`](../sub-skills/video-visualization/SKILL.md). For MOTChallenge scoring, route to [`sub-skills/evaluation/SKILL.md`](../sub-skills/evaluation/SKILL.md).

## Fast checks

1. Confirm the intended Python environment is the one running the task.
2. Confirm the base package imports: `from norfair import Detection, Tracker`.
3. If the task needs OpenCV drawing or video I/O, confirm `opencv-python` is installed.
4. If the task needs MOTChallenge scoring, confirm `motmetrics` and `pandas` are installed.
5. If you are unsure what the active environment contains, run `python scripts/check_norfair_env.py` with the relevant flags.

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: norfair` | The package is not installed in the active Python environment | Install the package with `pip install norfair` and rerun the environment check script. |
| `ModuleNotFoundError: filterpy` | Core tracking dependencies are missing | Install the base package or repair the environment before opening the tracking sub-skill. |
| `ImportError` mentioning OpenCV or `cv2` | The video extra is missing | Install `pip install norfair[video]` and route to the video-visualization sub-skill. |
| `ImportError` mentioning `motmetrics` or `pandas` | The metrics extra is missing | Install `pip install norfair[metrics]` and route to the evaluation sub-skill. |
| `pip install` changed the wrong environment | A different interpreter or prefix was targeted | Re-run installation and checks in the same environment that will run the skill. |
| `python scripts/check_norfair_env.py` fails on one route but not another | The optional extra for that route is missing | Install the missing extra only, rather than broad dev or benchmark dependencies. |

## Install guidance

Use the smallest install that matches the requested route:

```bash
pip install norfair
pip install norfair[video]
pip install norfair[metrics]
pip install norfair[video,metrics]
```

Do not install unrelated detector stacks, benchmark datasets, or GPU-only demo dependencies unless the task explicitly needs them.

## Recovery pattern

- If the task is core tracking only, install the base package and retry.
- If the task is about video or drawing, install the video extra and then open `sub-skills/video-visualization/SKILL.md`.
- If the task is about MOTChallenge scoring, install the metrics extra and then open `sub-skills/evaluation/SKILL.md`.
- If the task is about tracker shape or ReID failures, keep the install fix separate and then open `sub-skills/tracking-core/SKILL.md`.
