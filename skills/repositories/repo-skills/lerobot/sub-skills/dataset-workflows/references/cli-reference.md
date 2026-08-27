# Dataset CLI reference

All commands below are plans to adapt after `--help` verification in the target
environment. Dotted flags are parsed by draccus; quote JSON/list values in a shell.
Keep runs local and bounded unless Hub/network consent is explicit.

## Dataset tools and inspection

```bash
lerobot-edit-dataset --help
lerobot-dataset-viz --help
lerobot-imgtransform-viz --help
lerobot-convert-dcp --help
```

The dataset operation CLI requires `--operation.type`. Supported operation types
in the current parser are `delete_episodes`, `split`, `merge`, `remove_feature`,
`modify_tasks`, `convert_image_to_video`, `recompute_stats`, `reencode_videos`,
and `info`. Exact path flags are `--root` and `--new_root`; the latter is the
output base for split or exact output for other operations. `--repo_id` identifies
the source, `--new_repo_id` identifies a new output, and `--push_to_hub true` is a
network side effect that must be separately authorized.

Safe operation plans:

```bash
# inspect only; no mutation
lerobot-edit-dataset --repo_id <id> --root <root> \
  --operation.type info --operation.show_features true

# delete to a distinct output
lerobot-edit-dataset --repo_id <id> --root <src> \
  --new_repo_id <id>_filtered --new_root <dst> \
  --operation.type delete_episodes \
  --operation.episode_indices "[0, 2]"

# split by fractions or explicit episode lists
lerobot-edit-dataset --repo_id <id> --root <src> --new_root <out-base> \
  --operation.type split --operation.splits '{"train": 0.8, "val": 0.2}'
lerobot-edit-dataset --repo_id <id> --root <src> --new_root <out-base> \
  --operation.type split --operation.splits '{"train": [0,1], "val": [2]}'

# merge explicitly named compatible sources
lerobot-edit-dataset --new_repo_id <merged-id> --new_root <dst> \
  --operation.type merge --operation.repo_ids "[<id-a>, <id-b>]" \
  --operation.roots "[<root-a>, <root-b>]"

# image-to-video, with bounded processing
lerobot-edit-dataset --repo_id <image-id> --root <src> \
  --new_repo_id <video-id> --new_root <dst> \
  --operation.type convert_image_to_video \
  --operation.episode_indices "[0,1]" \
  --operation.max_episodes_per_batch 8 \
  --operation.max_frames_per_batch 2000

# stats in a distinct output (the current implementation may copy/rewrite data)
lerobot-edit-dataset --repo_id <id> --root <src> \
  --new_repo_id <id>_stats --new_root <dst> \
  --operation.type recompute_stats

# info-only visualization planning
lerobot-dataset-viz --repo-id <id> --root <root> --mode local \
  --episode-index 0
```

`delete_episodes`, split, merge, feature changes, conversion, stats, and video
re-encoding can read many files and write a complete new dataset. Do not omit
`--new_root` merely because a default is available. The helper
`scripts/dataset_operation_plan.py` prints an explicit dry-run and refuses to
execute any of these operations.

## Recording/training dataset flags

Dataset-related recording flags include `--dataset.repo_id`, `--dataset.root`,
`--dataset.fps`, `--dataset.num_episodes`, `--dataset.single_task`,
`--dataset.video`, `--dataset.streaming_encoding`,
`--dataset.video_encoding_batch_size`, `--dataset.encoder_queue_maxsize`,
`--dataset.encoder_threads`, `--dataset.rgb_encoder.<field>`, and
`--dataset.depth_encoder.<field>`. Recording and physical cameras belong to the
robot-control skill; this list is only the dataset handoff contract.

Training dataset selection commonly uses `--dataset.repo_id`, `--dataset.root`,
`--dataset.streaming`, `--dataset.repo_type`, `--dataset.episodes`,
`--dataset.exclude_episodes`, `--dataset.eval_split`,
`--dataset.video_backend`, `--dataset.depth_output_unit`,
`--dataset.image_transforms.enable`, and nested transform fields. Policy-specific
history is resolved by the training factory; validate the resulting feature keys
and offsets rather than hand-writing incompatible delta windows.

## Conversion and credentials

The v2.1 migration entry point is the module script
`convert_dataset_v21_to_v30.py`, not a project script entry in the current
`pyproject.toml`. Run `python -m lerobot.scripts.convert_dataset_v21_to_v30 --help`
when available in the installed package, or invoke the packaged script in a
checkout. Use `--repo-id`, `--root`, and `--push-to-hub=false` for a local trial.
It needs the dataset extra's `jsonlines` dependency and a v2.1 input.

Hub dataset loads, `StreamingLeRobotDataset` remote iteration, dataset viz against
a remote repo, and `push_to_hub` need network access. Private/gated data needs an
HF credential supplied through the normal Hub client (`HF_TOKEN` or login) or an
explicit token argument. Do not put tokens in logs, command transcripts, or
runtime skill files. `repo_type="bucket"` is for an HF Storage Bucket and is not a
substitute for a dataset repository id.
