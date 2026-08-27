# Troubleshooting ManiSkill trajectory and dataset workflows

## Quick diagnosis table

| Symptom | Likely cause | Safe fix |
|---|---|---|
| Replay/conversion says JSON is missing | `.h5` file is not paired with a sibling `.json` of the same stem | Stop. Locate or regenerate the JSON; do not guess `env_kwargs` for replay. Use `scripts/inspect_trajectory_bundle.py` to confirm. |
| Dataset loader fails on `trajectory.json` | `ManiSkillTrajectoryDataset` replaces `.h5` with `.json` and requires that file | Place the matching metadata JSON next to the `.h5` or use the original bundle. |
| New replay file is not where expected | Replay writes beside the input and appends obs/control/backend suffixes | Inspect the source directory and use the output stem pattern in `data-layout.md`. |
| Control-mode conversion fails or diverges | Only limited conversions are implemented; Panda is best supported | Replay without conversion first. If converting, use CPU replay and a supported original mode (`pd_joint_pos` or `pd_joint_delta_pos`). |
| `NotImplementedError` about GPU control conversion | GPU-parallel replay does not support changing control modes | Re-run with CPU backend for conversion, or keep the original control mode on GPU. |
| Assertion about env states and control conversion | `--use-env-states` cannot be combined with a different target control mode | Choose exact state replay without conversion, or conversion without `--use-env-states`. |
| CPU/GPU backend replay has lower success | CPU and GPU physics can diverge despite same seed/actions | Use `--use-first-env-state`, reduce parallelism, keep original backend for evaluation, or use `--use-env-states` when exact state observations matter. |
| Download script asks to create/remove/continue | Asset downloader is protecting local files | Ask the user. Use list/preview first; use `-y` or `MS_SKIP_ASSET_DOWNLOAD_PROMPT=1` only after approval. |
| Download hangs or fails | Network/Hugging Face/data host unavailable or asset is large | Keep the workflow user-controlled; retry only after confirming network/budget. Do not silently switch to `all`. |
| `convert_to_lerobot -h` fails before showing help | Converter imports optional packages at module import time | Install/verify `pandas` and OpenCV; for real conversion also verify `pyarrow` or full `lerobot`. |
| LeRobot conversion has no videos | Source trajectory lacks RGB observations | Replay first with an RGB/vision obs mode, then convert the replayed file. |
| Parquet write fails | `pyarrow` missing or incompatible | Install `pyarrow` or `lerobot`, then re-run the converter. |
| RecordEpisode produces no videos | `save_video=False`, render mode/backend unavailable, or video trigger never fires | Enable `save_video`, check render backend, and test a short video-only replay before a long run. |
| Assertion about `max_steps_per_video` in vectorized recording | GPU-parallel env with `save_video=True` needs fixed video cut length | Set `max_steps_per_video` to `max_episode_steps` or another fixed segment length. |
| Teleoperation window does not open | No display/GUI, missing Vulkan/display driver, or headless session | Teleop requires display, mouse, and keyboard. Use motion planning or scripted collection instead, or move to a GUI-capable host. |
| Teleop video generation takes a second pass | Teleop scripts replay recorded env states after collection when `--save-video` is requested | Let the second pass complete, or disable video and generate videos later with replay. |

## Missing `.h5` / `.json` pairs

Every normal replay, dataset-load, and conversion path needs both files. The JSON
is not optional metadata: it stores `env_id`, `env_kwargs`, episode reset seeds,
control modes, and source type. If only an `.h5` remains, safe options are:

1. Search for the matching `.json` in the same original recording/export folder.
2. Re-run the collection or replay that generated the `.h5`.
3. If a human insists on manual reconstruction, treat it as a custom forensic
   task and keep the result unverified until a short replay proves it.

Use:

```bash
python scripts/inspect_trajectory_bundle.py path/to/trajectory.h5
```

## Replay and control-mode conversion limits

The replay CLI can regenerate observations, rewards, and videos from saved
states/actions, but action conversion is not general robotics retargeting.

- Supported happy path: raw or teleop data from Panda-like `pd_joint_pos` replayed
  into easier-to-learn Panda joint/end-effector control modes on CPU.
- Limited reverse path: `pd_joint_delta_pos` to `pd_joint_pos`.
- Unsupported common cases: arbitrary robot families, mobile manipulators,
  dictionary-action wrappers not matching the original collection, GPU-parallel
  conversion, and conversion while forcing every env state.

If conversion fails, first replay with matching control mode and `--count 1` to
prove the bundle is readable. Then add one change at a time: target obs mode,
then reward recording, then target control mode, then backend migration.

## Download prompts and network dependence

`download_demo` and `download_asset` are intentionally user-controlled. The safe
progression is:

```bash
python scripts/preview_download_options.py --kind both --category scene --limit 20
python -m mani_skill.utils.download_demo
python -m mani_skill.utils.download_asset --list scene
```

Only after the user approves data size, network use, and output directory should
an agent run commands such as:

```bash
python -m mani_skill.utils.download_demo PickCube-v1 -o demos_cache
python -m mani_skill.utils.download_asset ReplicaCAD -y -o asset_cache
```

Avoid `all` unless the user explicitly asks for the full collection.

## Optional conversion dependencies

The LeRobot converter is separate from base trajectory replay. Troubleshoot in
this order:

1. `python -m mani_skill.trajectory.convert_to_lerobot -h`: proves module import
   and tyro CLI help work.
2. `python scripts/plan_lerobot_conversion.py trajectory.h5 out_dir`: checks the
   pair, dependency visibility, cameras, and command without writing data.
3. Install missing packages only after user approval. Minimal common packages are
   `pandas`, `pyarrow`, and OpenCV; full `lerobot` is useful but heavier.
4. Re-run conversion on a small copied or temporary output directory first.

## Recording output and video issues

When wrapping with `RecordEpisode`:

- Set `trajectory_name` deliberately if later scripts expect `trajectory.h5`.
- Use `avoid_overwriting_video=True` when resuming into a directory that may
  already have videos.
- Use `clean_on_close=True` unless debugging partial/incomplete episode output.
- If videos are too slow or too large, disable `render_substeps`, lower
  `video_fps`, use `render_mode=rgb_array`, or generate videos later via replay.
- If using a GPU-parallel env and saving video, set `max_steps_per_video`.

For motion-planning and teleoperation examples, trust the path printed by the
script after completion. Maintained runners may choose different layout order
than older prose examples.

## Teleoperation/display limitations

Click+drag teleoperation is not a headless data generator. It requires:

- A GUI/display-capable session.
- Mouse and keyboard input.
- A supported robot-specific teleop module.
- A task that can be solved by interactive subgoals and motion planning.

Use `h` in the viewer to print commands. Use `q` to quit cleanly so the
trajectory metadata is flushed. If a user only has a headless server, propose
motion-planning generated data, scripted policies, or recorded demo downloads
instead of trying to run the interactive teleop loop.
