# RoboCasa workflows

This reference distills the source converter and the reference-only subset and
rerender flows. It is a planning contract, not a runnable wrapper. Do not
bundle or execute the RoboCasa simulator, the source notebook, or a command
that can delete a user's data without an explicit review.

## 1. Decide what artifact is needed

| Request | Input condition | Route | Result and caveat |
|---|---|---|---|
| RGB-only LeRobot dataset | Existing HDF5 already has the required 256x256 RGB streams | Conversion | Five default feature families: 3 videos, state, action; language is frame task metadata |
| Fewer demos | Source has a `mask/<name>` list of demo IDs | Subset copy, then conversion | Preserves selected `data` groups and `data` attributes; missing IDs need a report |
| 256x256 plus depth/segmentation/calibration | Original HDF5 is commonly 128x128 and lacks some modalities | External simulator rerender, then conversion or a custom schema | Requires RoboCasa/robosuite assets and rendering; unsuccessful episodes are omitted |
| Keep all rerender modalities in LeRobot | Rerendered HDF5 has extra observation arrays | Custom feature schema | The default converter ignores extra keys; define and validate features first |

If the user has not chosen among these outcomes, stop at the decision point.
The default converter is not a general resize or modality synthesis tool.

## 2. External installation and asset preflight

For conversion-only work, create an isolated Python environment containing a
compatible LeRobot dataset API, `h5py`, NumPy, JSON support, and progress
reporting. Probe the actual installed LeRobot version and import the dataset
writer from `lerobot.datasets.lerobot_dataset`; the source checkout's imports
were observed at a particular snapshot and may not match every LeRobot release.

For subset or rerender work, additionally install the RoboCasa and robosuite
versions required by the source HDF5 `env_args`, the corresponding MuJoCo
runtime, and all RoboCasa assets. Verify, before touching data:

- the environment name and `env_kwargs` in `data.attrs['env_args']` parse as
  JSON;
- the named cameras exist and offscreen rendering can be initialized;
- the saved model XML and initial state are present for a representative demo;
- the renderer can produce RGB, depth, and the requested segmentation mode;
- the simulator's camera utility exposes intrinsic and extrinsic calculations;
- the chosen output directory is new or has a reviewed backup.

Do not treat an import-only RoboCasa probe as proof that assets or rendering
work. Do not download datasets/assets, start a simulator, or render during
skill drafting or a static verification pass.

## 3. Safe conversion plan

Use an explicit command plan equivalent to:

```text
python <self-contained conversion entry point> \
  --raw-dir <directory containing HDF5 files> \
  --repo-id <metadata dataset identifier> \
  --local-dir <new output directory>
```

The source command accepts `--raw-dir`, `--local-dir`, and `--repo-id`. There
is no source flag for push-to-Hub, subset selection, depth, segmentation,
resizing, rerendering, resume, or filtering. A caller must not invent those
flags and must not assume a shell launcher supplies them.

Before allowing the run, make the following plan explicit:

1. Resolve `raw_dir` to a directory and enumerate only intended `*.hdf5`
   inputs. Ensure the output directory is not inside the input tree.
2. Inspect the HDF5 contract described in [data-formats.md](data-formats.md).
3. If `local_dir` exists, stop for backup/approval: the source behavior uses
   recursive deletion (`rmtree`) before dataset creation.
4. Confirm the LeRobot writer API and feature schema. Use a separate metadata
   `repo_id`; it does not authorize network publishing by itself.
5. Convert in deterministic source/dataset/demo order where reproducibility
   matters. Record input files, selected demos, frame counts, skipped/failing
   demos, and output metadata.
6. Finalize only after all episodes are saved, then inspect metadata and a
   sample episode. Do not delete input HDF5s on failure.

The default writer initializes `robot_type=PandaOmron` and `fps=20`. It writes
three video features with shape `(256, 256, 3)` and channel order
`height,width,channel`; state and action are float32 vectors of shapes `(9,)`
and `(12,)`. The task string is repeated per frame from `ep_meta['lang']`.

### Frame alignment rule

For each demo, the image arrays, action array, and three state components must
have the same first dimension. Use that common demo length. Reject or isolate
a demo when a component is shorter, when an image is not HWC RGB, or when the
language metadata is absent/invalid. Do not pad, truncate, transpose, resize,
or cast a malformed source silently; a custom repair policy must be recorded
and applied before the writer.

### Output replacement rule

The observed source implementation deletes `local_dir` before calling the
LeRobot dataset constructor. Treat this as an unconditional destructive
replacement, including if the path contains unrelated files. Safe operation
requires a new path or a reviewed backup, a path containment check, and an
explicit confirmation. A crash after deletion can leave no usable output.

## 4. Subset-copy plan (reference-only)

The subset intent is:

1. Open one source HDF5 read-only.
2. Find `mask/<subset_name>` such as `30_demos` or `100_demos`.
3. Decode byte IDs to text when necessary and preserve order for the report.
4. Compare IDs with `data` group names. Report missing and duplicate IDs.
5. Create a new HDF5 and a `data` group.
6. Copy every attribute from source `data` to destination `data`, especially
   `env_args`.
7. Copy only the requested demo groups into destination `data`, preserving
   their attributes and all nested arrays.
8. Re-open the result read-only and assert that the selected IDs and
   `env_args` survived before conversion.

The subset notebook is intentionally not bundled. A copy operation can be
large and can overwrite a destination if implemented carelessly. Use a
separate output path, do not modify the original, and treat a missing `mask`
or subset name as a blocking validation error rather than selecting all demos.

## 5. Rerender plan (reference-only and expensive)

Rerendering is a simulator workflow, not a normal CPU conversion. The
source-derived flow is:

1. Open the original HDF5 read-only and parse `data.attrs['env_args']`.
2. Override environment kwargs for offscreen observations: depth enabled,
   `camera_heights=256`, `camera_widths=256`, and an explicit segmentation
   mode such as `element`; set renderer/offscreen flags and avoid early
   termination while configuring the playback environment.
3. Create the RoboCasa environment and restore each demo's saved model XML and
   initial simulator state.
4. Warm up with ten fixed dummy actions before collecting observations.
5. For every recorded action, capture RGB, convert normalized MuJoCo depth to
   world-depth using the simulator near/far values, compute camera matrices,
   append simulator state/reward/done, then step the recorded action.
6. Consider an episode successful when the terminal condition or environment
   success check is true. Save only successful episodes, carrying model XML,
   JSON `ep_meta`, observations, actions, absolute actions, dones, rewards, and
   simulator states.
7. Close input/output files. If no episode succeeded, the reference flow
   deletes the output HDF5; this is another destructive behavior requiring a
   dedicated output directory and pre-run approval.

Do not present this sequence as guaranteed reproducibility. RoboCasa task
assets, environment versions, physics, renderer backend, and saved XML all
matter. A rerendered dataset can differ from the source and can contain fewer
episodes. Rerendering must be separately validated before it becomes converter
input.

## 6. Post-rerender conversion boundary

The default LeRobot conversion consumes the three RGB keys, three state pieces,
actions, and `ep_meta.lang`. It does not consume the rerendered depthW,
segmentation, intrinsic, extrinsic, relative-extrinsic, reward, done, absolute
action, or simulator-state arrays. If those are required downstream:

- retain the rerendered HDF5 as the source of truth;
- define a deliberate LeRobot feature map for each retained modality;
- specify dtype, shape, axis names, camera name, and units/convention;
- confirm all added arrays align with the action/frame timeline;
- test one episode before a full write.

Do not imply that a successful RGB conversion proves depth or segmentation
availability.
