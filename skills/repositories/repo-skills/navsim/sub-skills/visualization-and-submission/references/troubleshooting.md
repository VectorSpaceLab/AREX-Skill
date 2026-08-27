# Visualization and submission troubleshooting

Use this as a diagnosis table. Fix the first failing layer; do not mask a
missing dataset or a server-side failure by retrying a long runner.

## Install, import, optional dependencies, and backend

| Symptom | Likely cause | Recovery |
|---|---|---|
| `import navsim.visualization...` fails | NAVSIM is not installed in the active Python, or the dependency set is incomplete | Activate the intended Python 3.9+ environment, install the package according to its documented environment plan, and run a minimal import. Do not diagnose a dataset path until the import succeeds. |
| `ModuleNotFoundError` for `matplotlib`, PIL, OpenCV, Shapely, or nuPlan | Visualization imports optional-looking packages at module import time; BEV also needs nuPlan geometry/map classes | Install the package's compatible runtime requirements. If only pickle validation is needed, use the bundled standard-library validator instead of importing visualization. |
| plots fail on a headless host | Matplotlib selected an interactive GUI backend | Select a non-interactive backend such as `Agg` before importing pyplot, save figures, and close them. This does not fix missing sensor data. |
| CUDA is unavailable while plotting | Plotting itself is CPU/matplotlib work; CUDA is not a visualization prerequisite | Use CPU for rendering. CUDA matters only if the chosen agent/checkpoint is executed to produce a trajectory; do not claim learned-agent parity from a plot-only check. |
| map imports fail after a dependency upgrade | nuPlan-devkit/geospatial packages are incompatible or map assets are absent | Recheck package compatibility and `NUPLAN_MAPS_ROOT`/map version with the setup route. For camera-only plots, omit map layers only if the application can safely avoid `add_configured_bev_on_ax`; do not fabricate a map. |

A data-independent check is to import the public plot module and run the
validator's `--help`. A rendered plot or GIF requires real scene inputs.

## Data, sensor, and configuration validation

| Symptom | Likely cause | Recovery |
|---|---|---|
| `SceneLoader` finds no scenes | Wrong `OPENSCENE_DATA_ROOT`, split subdirectory, log root, token filter, or route filter | Print/inspect the resolved paths and selected split. Confirm `navsim_logs/<data-split>` and `sensor_blobs/<data-split>` exist and that the filter has candidates. |
| synthetic scenes assert missing | A two-stage filter has `include_synthetic_scenes=True` but `synthetic_scenes_path` or `synthetic_sensor_path` is missing/wrong | Supply the matching synthetic roots for the selected split. Warmup and private challenge roots are not interchangeable. Stop if the user has not supplied authorized private data. |
| `FileNotFoundError` for image/LiDAR blob | The scene metadata and sensor root do not correspond, or the requested modality was not downloaded | Check the split-specific blob root and `SensorConfig`; use no-sensor loading only for blind-agent/API checks, not camera/LiDAR rendering. |
| camera panel is blank or projection raises on `None` | Camera image/calibration was not loaded | Request the camera in `SensorConfig`, verify the eight camera identifiers, and load the matching sensor blob. A blank `Camera()` is an input problem. |
| BEV map layer raises map API errors | Map root/version is missing or the scene map is unsupported | Validate nuPlan map installation and scene map name. Temporarily render annotations/LiDAR only if map-free output is acceptable, and label that omission. |
| plots show the wrong frame | `frame_idx` is not the current frame | Use `scene.scene_metadata.num_history_frames - 1` for the current frame; explicitly choose another history/future index and check bounds. |
| LiDAR overlay crashes on an empty or constant cloud | The color helper expects points and normalizable variation | Check the point-cloud shape and finite values before plotting. Use the default distance coloring for ordinary clouds; guard empty/constant clouds in a local custom wrapper rather than modifying data silently. The `color_element="none"` branch in this release is also fragile, so test that choice before relying on it. |

## CLI, Hydra, and API misuse

| Symptom | Likely cause | Recovery |
|---|---|---|
| Hydra reports a missing mandatory value | `team_name`, `authors`, `email`, `institution`, `country`, `experiment_name`, or a path was left as `???` | Supply each required override explicitly. Use `--help`/composition inspection first; do not launch a scene loop to discover a missing scalar. |
| override is ignored | The key or config group name is wrong, or a shell variable was not exported/expanded | Use exact keys such as `train_test_split`, `agent`, `synthetic_sensor_path`, `synthetic_scenes_path`, and metadata names. Quote values containing spaces and print the final command. |
| runner changes the working directory or writes unexpected files | Hydra output/run directory behavior | Use a dedicated writable output root and inspect the composed config before running. Treat generated Hydra logs as disposable and do not put credentials in them. |
| `AttributeError`/shape error from a custom plot | Wrong object passed (a `Frame` where a `Scene` is expected, or an array where `Lidar`/`Annotations` is expected) | Follow the public signatures: scene-level plotters take `(scene, frame_idx)`; BEV adders take an Axes and a frame's typed object; camera adders take a camera plus the relevant object. |
| GIF creation fails with `IndexError` | No frame indices were supplied | Validate a non-empty, in-range `frame_indices` list before calling `frame_plot_to_gif`. |
| the validator says a trajectory is malformed | Prediction value is not a NAVSIM-like trajectory, has no `.poses`, or poses are not `(N, 3)` | Return `Trajectory(poses, matching_sampling)` from `compute_trajectory`; keep local x/y/heading order and sampling length consistent with the agent/config. |

## Submission-specific failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| validator reports missing metadata | One of the five required fields is absent, empty, or still `MUST_SET` | Set `team_name`, `authors`, `email`, `institution`, and `country / region` in the generator config; regenerate, then validate. |
| `country` appears present but validator/server rejects it | The pickle key is `country`, `country_region`, or another spelling | The generator writes the exact key `"country / region"`; do not rename it. The Hydra override remains `country`. |
| stage container has the wrong type | A dict was written instead of a one-element list of dicts, or stage maps were flattened | Preserve `first_stage_predictions: [first_stage_dict]` and `second_stage_predictions: [second_stage_dict]`. Each token maps to a trajectory object. |
| both stage maps are empty or coverage is unexpectedly low | Agent exceptions were logged and the runner continued; data or checkpoint inputs failed per scene | Stop and inspect the first per-token exception. Fix the agent/sensor/data issue and regenerate; an apparently successful process is not a valid submission. |
| generation aborts: `requires_scene has to be False` | A privileged agent such as a human/annotation-dependent agent was selected | Use a sensor-only agent whose public contract computes from `AgentInput`. Do not disable the guard or leak annotations into submission. |
| warmup local and server scores differ | Split/cache mismatch, different metric-cache path, agent/checkpoint, proposal sampling, or evaluation policy | Re-run the parity checklist with `warmup_two_stage` everywhere and the same cache path/config. Ask the evaluation route to diagnose EPDMS details. |
| private runner cannot import its loader or data | Private challenge assets/permissions are unavailable | Stop. Do not substitute public data and do not attempt to reconstruct private scenes. Use the authorized private-aware environment only. |
| server says invalid token, failed, or no result | External login/model-hosting/submission issue or server validation failure | Confirm the hosted filename is `submission.pkl` and the model reference is correct, then follow the competition's external support process. Do not upload from this skill or retry repeatedly under submission limits. |

The validator loads pickle files and therefore must be run only on trusted local
artifacts. It performs no network access, upload, dataset loading, or benchmark
execution.
