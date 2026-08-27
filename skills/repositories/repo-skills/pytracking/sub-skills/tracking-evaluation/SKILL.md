---
name: tracking-evaluation
description: "Configure and run PyTracking trackers on datasets, videos,
  webcams, and experiment functions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# tracking-evaluation

Use this sub-skill when a task is about planning or running PyTracking evaluation/runtime commands:

- run a tracker on a full dataset or one dataset sequence
- run a tracker on a video file or webcam feed
- write or use an experiment function that returns `trackerlist(...)` and `get_dataset(...)`
- identify dataset aliases, local configuration fields, debug/Visdom behavior, and result locations
- construct a safe command without launching trackers, cameras, datasets, or GUI windows

Do **not** use this sub-skill for:

- result analysis, plots, GOT-10k/TrackingNet submission zips, or VOT toolkit integration: route to `analysis-and-packaging`
- LTR model training or train-setting modification: route to `ltr-training`
- implementing, registering, or deeply debugging tracker/parameter modules: route to `tracker-development`

## Operating sequence

1. Read [workflows](references/workflows.md) for the relevant mode and use [the command builder](scripts/build_tracking_command.py) to print a candidate command. The helper only builds commands.
2. Read [datasets and results](references/datasets-and-results.md) before launching a dataset run. Confirm the dataset alias, sequence name/index, `local.py` paths, network/checkpoint path, and expected result directory.
3. Read [API reference](references/api-reference.md) if you need Python calls instead of CLI commands.
4. Read [troubleshooting](references/troubleshooting.md) before retrying any failed run.

## Minimal execution gates

- The target environment must import `pytracking` and `ltr`; full network-backed tracker runs usually require a CUDA-capable PyTorch stack and pretrained checkpoints.
- `pytracking/evaluation/local.py` must exist and contain the dataset, network, and result paths needed by the chosen alias. Some VOS, AVisT, and LaGOT aliases require extra local fields; see [datasets and results](references/datasets-and-results.md).
- A tracker command's `tracker_name` and `tracker_param` are import names, not display labels. `Tracker` imports `pytracking.tracker.<tracker_name>` and `pytracking.parameter.<tracker_name>.<tracker_param>`.
- Full dataset evaluations, webcam feeds, video GUI windows, and Visdom sessions are side-effecting and can be long-running. Confirm user approval, data paths, checkpoint availability, device/budget, and GUI/service availability before executing emitted commands.

## Quick command planning

From this sub-skill directory, generate but do not run a dataset command:

```bash
python scripts/build_tracking_command.py dataset --tracker dimp --param dimp50 --dataset otb --sequence Soccer --debug 0
```

List accepted dataset aliases:

```bash
python scripts/build_tracking_command.py --list-datasets
```

Generate a video command with a numeric initialization box:

```bash
python scripts/build_tracking_command.py video --tracker atom --param default --videofile /path/to/video.mp4 --optional-box 100 80 60 40
```
