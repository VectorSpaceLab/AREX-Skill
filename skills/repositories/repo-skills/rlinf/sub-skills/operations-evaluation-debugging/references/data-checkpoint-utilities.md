# Data and checkpoint utility guardrails

RLinf ships utilities for replay buffers, LeRobot datasets, dual-Franka data repair, standalone framework evaluation, and checkpoint conversion. Many are useful for operations, but some mutate files or require heavyweight dependencies. Use this reference to decide whether to inspect, copy, convert, or stop for user approval.

## General safety rules

- Treat logs, checkpoints, replay buffers, LeRobot datasets, and robot demonstration data as user artifacts.
- Prefer read-only inspection first: list files, validate metadata JSON, count trajectories/episodes, and inspect shapes before any write.
- Use a new output directory for conversions, merges, splits, videos, and visualizations.
- When a utility supports copy-vs-move, choose copy by default.
- Do not delete, merge, split, backfill, or convert live robot data without explicit approval and a rollback plan.
- If a utility requires optional dependencies such as `pyarrow`, `Pillow`, `opencv-python`, `safetensors`, JAX/Orbax, or simulator packages, report the missing dependency instead of broad-installing extras.

## Replay buffer utilities

RLinf replay buffers can contain rank-sharded trajectory directories or a single merged buffer with:

```text
<buffer>/
├── metadata.json
├── trajectory_index.json      # legacy typo `trajector_index.json` may also exist
└── trajectory_<id>_<weights-id>.pt|.pkl
```

Operational checks:

- Validate `metadata.json` has a trajectory format (`pt` or `pkl`), size/trajectory counter, and total sample counts.
- Validate the index lists every trajectory file and that ids are unique.
- In rank-sharded buffers, inspect every `rank_*` directory before merging.
- If splitting by trajectory count, confirm the requested count is not larger than available ids.

Mutation guardrails:

- Merge/split utilities can move files unless copy mode is requested; default to copy mode when advising users.
- Visualizers are safer than merge/split but may write images/videos; use a new visualization directory.
- Headless visualization is preferable on servers without a display.

Typical uses:

- **Audit before RLPD/offline training:** metadata/index consistency and rough trajectory counts.
- **Prepare a portable sample:** copy-split a small subset into a new directory.
- **Debug a failed real-world run:** visualize a handful of trajectories before blaming policy/model code.

## LeRobot utilities

LeRobot datasets use Parquet data plus JSON metadata:

```text
<dataset>/
├── meta/
│   ├── info.json
│   ├── episodes.jsonl
│   ├── tasks.jsonl
│   └── stats.json
└── data/
    └── chunk-000/
        ├── episode_000000.parquet
        └── ...
```

RLinf data collection can export episode data to LeRobot while preserving key fields such as `image`, `extra_view_image`/numbered extra views, `state`, `actions`, `timestamp`, `episode_index`, `task_index`, `done`, and `is_success`.

Operational checks:

- Confirm `meta/info.json` and `meta/episodes.jsonl` exist before assuming a valid dataset.
- Confirm image columns and action/state dimensions match the model family.
- Check `stats.json` or recompute normalization stats only when the user asks; norm stats affect policy action scaling.
- For MP4/JPEG expansion, budget storage. Videos can be much larger than source metadata.

Visualization behavior distilled from RLinf utilities:

- A LeRobot visualizer can expand datasets into one folder per episode, write per-step images and text metadata, and optionally export per-view and merged MP4 videos.
- MP4 export requires OpenCV; image export requires Pillow; parquet reading requires PyArrow.
- Multi-view videos are stitched with labels; two views become a horizontal strip, three or four views become a grid, five or more become a horizontal strip.

## Dual-Franka data utilities

Dual-Franka helper utilities repair or manipulate LeRobot-style datasets for bimanual/real-world workflows. Treat them as high-risk because they can delete rows, merge datasets, or backfill transforms.

Use only after confirming:

- The dataset is a copy or the user explicitly approves mutation.
- The robot embodiment, camera layout, and TCP/rotation convention are correct.
- The requested change is idempotent or a backup exists.
- A small sample can be inspected after transformation.

Common operations:

- Backfill TCP rotations or derived transforms.
- Merge LeRobot datasets after confirming task and schema compatibility.
- Delete bad LeRobot episodes/segments only by explicit user selection.

## Episode collection artifacts

RLinf's episode collection wrapper can emit two formats:

- **Pickle:** one file per episode, named by rank/env/episode/success state, storing raw observations/actions/rewards/dones/infos.
- **LeRobot:** Parquet episodes plus metadata, suitable for LeRobot training/eval pipelines.

Success detection checks `success_once`, `success_at_end`, and `success` in final info, episode info, and root info. If no success keys exist, it falls back to an internal episode success flag. When diagnosing missing successes, inspect the info schema before changing reward code.

## Real-robot replay buffer collection

Real-robot collection stores successful demonstrations in `TrajectoryReplayBuffer` form. It may also write LeRobot data in parallel when data collection is enabled.

Before using collected data:

- Verify the target number of successful demonstrations and trajectory count.
- Check `intervene_flags`; they mark expert intervention data for RLPD.
- Inspect a small sample with a visualizer.
- Confirm robot-specific action dimension, gripper/no-gripper convention, and camera resolution.

Do not relaunch real-robot collection or teleoperation from this sub-skill. Route setup and hardware execution decisions to the appropriate embodied/hardware guidance and require user approval.

## Standalone evaluation scripts

Standalone framework eval utilities exist for OpenPI and Dexbotic workflows. They run outside RLinf's distributed embodied evaluation pipeline and are useful when a user needs framework-native metrics:

- OpenPI: LIBERO, MetaWorld, CALVIN.
- Dexbotic: LIBERO.

Guardrails:

- They can be slower than RLinf distributed eval; single-GPU OpenPI evaluations may take hours.
- They require framework-specific Python paths, config names, model checkpoint paths, action chunks, denoise steps, and video settings.
- For RL-tuned flow policies, `num_steps` and `action_chunk` should match the RL training config; otherwise metrics are not comparable.
- Use standalone eval after RLinf eval/log diagnosis suggests a framework-level or per-task granularity question, not as the default smoke test.

## Checkpoint converter families

| Family | Input | Output | Main hazards |
| --- | --- | --- | --- |
| FSDP DCP to PT | Distributed `.distcp` checkpoint directory | Consolidated `.pt` state dict | Requires matching model/config and enough CPU/GPU memory. Skip if `full_weights.pt` already exists and is valid. |
| FSDP PT to HF/safetensors | Consolidated `full_weights.pt` plus model config | HuggingFace-style directory/safetensors | LoRA merge policy, model type, base model path, and save helper must match. |
| Megatron sharded to HF | Megatron actor checkpoint | Middle-file then HF directory | Tensor/pipeline/expert parallel sizes, model name, and process count must match original training. Intermediate files can be large. |
| OpenPI JAX/PyTorch/RLinf/SFT conversions | Orbax/JAX, OpenPI PyTorch, OpenPI_RLinf, or SFT checkpoints | OpenPI_RLinf, OpenPI PyTorch, or deploy format | Norm stats must be copied verbatim; dtype may be a real cast; some modes require a reference model for missing heads/shape validation. |

Conversion planning checklist:

1. Identify source checkpoint layout and target consumer.
2. Confirm model family and config name.
3. Confirm parallel sizes and LoRA/value-head settings when relevant.
4. Confirm dtype and norm-stat policy.
5. Choose a new output directory.
6. Run a read-only artifact check after conversion and only then plan evaluation.
