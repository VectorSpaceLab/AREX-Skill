# Training Troubleshooting

## Purpose

Use this reference when `lumi train`, `lumi eval`, or the cloud helpers fail on
config, run-directory, or cloud setup issues.

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `model.type should be set on the custom config.` | The config file does not declare a model family | Add `model.type` and choose `fasterrcnn` or `ssd`. |
| `Could not find checkpoint in '...'` during eval or checkpoint creation | The run directory does not yet contain checkpoint files | Wait for training to write a checkpoint or check the `train.job_dir` / `train.run_name` values. |
| `job_dir should be set` or `run_name should be set` | Eval cannot locate the run directory | Set both keys in the config before retrying. |
| Training starts but no checkpoints are written | `train.job_dir` is missing or logging is disabled | Set `train.job_dir` and confirm logging is enabled. |
| `InvalidDataDirectory` while training | The dataset reader cannot locate the TFRecords or source layout | Route back to dataset preparation and fix the dataset path first. |
| `Tried to load 0 config files` | The config list is empty | Pass at least one `--config` file. |
| Cloud command says the gcloud extras are missing | `luminoth[gcloud]` is not installed | Install the optional Google Cloud dependency group. |
| Cloud command reports forbidden access or missing APIs | The service account or GCP project setup is incomplete | Enable the required APIs and confirm the credentials and project match. |
| Cloud command cannot find the region | The `--region` value is invalid for the project | Choose a valid Google Cloud region. |
| TensorBoard has no useful graphs | Training did not write summaries or the log directory is wrong | Confirm `train.job_dir` and `train.run_name`, then point TensorBoard at the job directory. |

## Recovery workflow

1. Run `python scripts/check_config_keys.py --config ./config.yml --mode train`.
2. Fix the config keys until the script reports success.
3. If the error is about the dataset layout, hand the task back to the
   dataset-preparation sub-skill.
4. If the error is about a trained checkpoint, hand the task to checkpoints.
5. If the error is about inference after a finished run, hand the task to
   prediction.

## Notes

- `lumi eval` watches for new checkpoints by default; use `--no-watch` if you
  only want a single pass.
- `CUDA_VISIBLE_DEVICES` can be used to select a GPU on supported systems.
- Cloud jobs are optional and depend on external credentials and project state.
