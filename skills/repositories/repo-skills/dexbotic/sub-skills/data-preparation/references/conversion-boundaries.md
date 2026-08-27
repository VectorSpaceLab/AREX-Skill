# Conversion boundaries

The repository contains adapters for LeRobot-like parquet/video trees, RLDS/TFDS trajectories, and several robot datasets. These converters are format-specific and often require external packages such as parquet readers, TensorFlow/TFDS, video codecs, or LeRobot. The safe operating rule is:

- Inspect input metadata and run a bounded conversion on a tiny fixture first.
- Write output to a new directory; never overwrite raw demonstrations.
- Preserve episode boundaries and use stable, relative output references where the deployment data root will be mounted.
- Align every camera frame and state/action row by frame index or an explicitly documented timestamp policy.
- Record skipped rows/episodes and the reason; do not silently fill missing observations with zeros unless the model contract explicitly allows it.
- Re-run the validator on generated JSONL and inspect a handful of records before training.

The bundled `convert_lerobot_to_dexdata.py` is a conservative parquet-to-JSONL adapter for a simple LeRobot tree. It does not copy or transcode videos and intentionally requires explicit camera columns. The RLDS converter is not bundled because its `dlimp`, TensorFlow, TFDS, and codec stack is external and the source utility is reference-oriented; install and verify that stack separately if RLDS is selected.

For SO-101, XLeRobot, and DOS-W1, conversion is data-only and belongs to [evaluation-deployment](../../evaluation-deployment/SKILL.md). The robot bridges, camera capture, serial ports, and network control are never required for data validation.

## Minimal input shape for the bundled adapter

```text
input/
  meta/tasks.jsonl       # each line: {"task_index": 0, "task": "..."}
  data/<chunk>/*.parquet
```

The adapter expects `task_index`, `frame_index`, `observation.state`, and `action` columns. It emits JSONL records with `state`, `action`, `prompt`, `is_robot`, and optional `images_N` records when camera references are supplied by the caller. For project-specific schemas, use the validator as a preflight rather than pretending this adapter is universal.
