# Plexe dashboard workflow

This reference explains how to launch the dashboard and how the saved-run browser reads the
filesystem.

## Launch command

```bash
python -m plexe.viz --work-dir ./workdir
```

Optional flags:

- `--port` controls the Streamlit port, default `8501`.
- `--refresh` controls auto-refresh in seconds, default `2`.

## Environment variables

The dashboard reads these environment variables:

- `MBS_WORK_DIR`: absolute or relative workdir path passed by the launcher
- `MBS_REFRESH_INTERVAL`: dashboard refresh interval in seconds

The launcher sets both before starting Streamlit.

## Workdir discovery rules

The dashboard scans the workdir for experiment directories at these depths:

1. `workdir/<dataset_name>/checkpoints/`
2. `workdir/<dataset_name>/<timestamp>/checkpoints/`

Each discovered experiment is summarized into a sidebar item grouped by dataset name.

## What the dashboard expects

### Checkpoints

Checkpoint files live under `checkpoints/*.json`.
The latest checkpoint drives the experiment status, current phase, and progress summary.

### Reports

The dashboard reads generated YAML reports from `work_dir/.build/reports/`.
These reports drive the overview, data-understanding, preparation, baseline, and evaluation tabs.

### Packaged model

The package tab expects `model/` and optionally `model.tar.gz` under the experiment root.
It then reads:

- `model/model.yaml`
- `model/schemas/input.json`
- `model/schemas/output.json`
- `model/predictor.py`
- `model/src/pipeline.py`

## Tab map

| Tab | What it shows |
| --- | --- |
| Overview | phase timeline, status, metric, and best performance |
| Data Understanding | checkpoint summary for layout, stats, task analysis, and metric selection |
| Data Preparation | split and sample artifacts |
| Baselines | baseline model summary |
| Search Tree | search journal, performance trend, and insights |
| Evaluation | final metrics, diagnostics, robustness, and recommendations |
| Model Package | package metadata, schemas, predictor code, and feature pipeline |

## Useful local checks

- `scripts/inspect_workdir.py <work_dir>` for a text summary.
- `scripts/check_env.py --dashboard` to confirm the dashboard module imports and the CLI help parses.

## Failure symptoms

- Empty sidebar: no saved experiments found or the workdir path is wrong.
- Warnings about missing checkpoints: the run is incomplete or the checkpoint directory was removed.
- Model package tab shows "Model not yet packaged": the final packaging phase never completed.
- Rendering errors inside the tabs: one of the checkpoint or YAML files is malformed.

