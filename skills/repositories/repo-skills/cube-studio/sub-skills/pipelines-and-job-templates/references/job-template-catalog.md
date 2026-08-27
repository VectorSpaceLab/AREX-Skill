# Job template catalog

CubeStudio's job-template system groups reusable containerized tasks into named families that can be registered in the UI and reused in pipelines.

## Template directory contract

A template family normally contains:

- `Dockerfile` — image definition for the template runtime
- `build.sh` — the documented image build entry point
- `launcher.py` or `start.py` — the command-line entry point used inside the template image
- `README.md` — user-facing usage and registration notes
- optional JSON files — sample input/output, launch args, or config payloads

## Built-in families observed in this repository

| Family | Purpose | Notes |
| --- | --- | --- |
| `dataset` | Data copy / export / simple dataset operations | Uses a launcher with file or cache inputs. |
| `datax` | Data transfer and source-target conversion | Includes example JSON payloads for MySQL, PostgreSQL, Hive, and ClickHouse. |
| `demo` | Minimal example of task I/O and metrics output | Safe for explaining how result files and metrics are written. |
| `deploy-service` | Service packaging / deployment template | Often paired with model or API deployment workflows. |
| `model_download` | Retrieve model artifacts | Good reference for fetch-and-stage behavior. |
| `model_offline_predict` | Offline inference / batch prediction | Includes custom prediction code and RabbitMQ pattern variants. |
| `model_register` | Register a model artifact | Often used after training or conversion. |
| `pytorch` | PyTorch-based training or demo tasks | Useful for framework-specific launcher patterns. |
| `ray` / `ray_sklearn` | Distributed processing and classical ML | Includes CPU and GPU variants for Ray. |
| `tf` | TensorFlow task template | Common for training and inference examples. |
| `video-audio` | Multimedia processing | Includes task metadata suitable for rich I/O examples. |
| `volcano` | Volcano-scheduled batch jobs | Useful for GPU / batch scheduling examples. |
| `xgb` | XGBoost-style training or evaluation | Common classical ML example. |
| `yolov8` | Vision template family | Includes example YAML manifests for a vision workflow. |

## Args schema distilled from the README

Top-level object:

- keys are display groups
- each group maps to a dict of fields
- each field describes one launch parameter

Common field keys:

- `type`: `int`, `str`, `text`, `bool`, `enum`, `float`, `multiple`, `date`, `datetime`, `file`, `dict`, or `list`
- `item_type`: element type for enum / multiple / list-style fields
- `label`: human-readable label
- `require`: whether the field is required
- `choice`: allowed values for enum / multiple
- `range`: numeric range string
- `default`: default value
- `placeholder`: help text shown in the UI
- `describe`: longer note for the UI or documentation
- `editable`: whether the field may be changed

## Practical guidance

- Treat `build.sh` and launchers as reference material, not as a generic validation step.
- Use the bundled validator script to check args payload shape before handoff or review.
- Prefer template examples that are small, deterministic, and free of long-running or external side effects.
- Use `job-template/job/demo` when explaining metrics, output files, and minimal task I/O patterns.

## Routing hints

- If a task is mostly about the DAG or runtime pipeline object, use `pipeline-workflows.md` first.
- If a task is mostly about resource selectors or notebook images, route to the notebook/image sub-skill.
- If a task is mostly about model deployment, route to the serving sub-skill.
