# Troubleshooting

## Purpose

Use this reference for cross-cutting Luminoth failures that are not specific to
just one sub-skill.

## High-signal failure modes

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `Luminoth requires a TensorFlow >= 1.5 installation` or import fails before `lumi` runs | TensorFlow is missing or too old for this package | Install TensorFlow 1.x first, or use a `luminoth[tf]` / `luminoth[tf-gpu]` install that matches your backend. |
| `tensorflow.contrib` deprecation warnings | Expected on TensorFlow 1.x code paths | These warnings are noisy but not fatal for the supported snapshot. Stay on TF 1.x for this skill. |
| `lumi cloud gc ...` says the gcloud extras are missing | `luminoth[gcloud]` is not installed | Install the Google Cloud extras and provide a valid service account JSON through `GOOGLE_APPLICATION_CREDENTIALS`. |
| Cloud commands mention missing Compute Engine, ML Engine, or Storage APIs | GCP project setup is incomplete | Enable the APIs the command mentions and confirm the credentials belong to the intended project. |
| `Please install ffmpeg before making video predictions` | FFmpeg is not installed system-wide | Install FFmpeg if you need video output. Image-only prediction does not need it. |
| `Neither checkpoint not config specified, assuming \'accurate\'.` | Prediction or web command fell back to the default checkpoint | Explicitly pass `--checkpoint` or `--config` if you want a different model. |
| `model.type should be set on the custom config.` | Training or eval config is missing the model family | Fix the YAML config before retrying. |
| `job_dir should be set` or `run_name should be set` | Eval or checkpoint workflows need a run directory but the config does not define it | Set `train.job_dir` and `train.run_name`, or switch to the sub-skill that creates the run/checkpoint first. |
| `Could not find checkpoint in '...'` | The training run directory has no checkpoint files yet | Wait for training to write a checkpoint, or inspect the run directory before packaging/predicting. |
| `Only one of \`only-class\` or \`ignore-class\` may be specified.` | Prediction filters are mutually exclusive | Pick one filter mode. |
| `No files to predict found. Accepted formats are ...` | The provided path list contains no supported image/video files | Verify extensions and file paths, or point the command to a directory that contains supported media. |
| `Checkpoint directory '...' already exists` | The checkpoint tar import/download target already exists locally | Delete the stale directory or choose a different local checkpoint home. |

## Cross-skill handoff guidance

- If the problem is dataset layout or `InvalidDataDirectory`, route to
  `sub-skills/dataset-preparation/SKILL.md`.
- If the problem is run configuration, `train.job_dir`, `train.run_name`, or
  Google Cloud setup, route to `sub-skills/training/SKILL.md`.
- If the problem is checkpoint discovery, alias collisions, tar import/export,
  or the local checkpoint index, route to `sub-skills/checkpoints/SKILL.md`.
- If the problem is image/video input selection, ffmpeg, or the Flask demo,
  route to `sub-skills/prediction/SKILL.md`.

## Skill freshness checks

If the repository commit or package version no longer matches
`references/repo-provenance.md`, treat this generated skill as stale and refresh
it before trusting the route map.
