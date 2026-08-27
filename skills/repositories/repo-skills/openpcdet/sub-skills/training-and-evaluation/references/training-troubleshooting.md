# Training and Evaluation Troubleshooting

## Before launching a job

- Runtime: compiled CUDA ops and spconv import.
- Config: model/dataset/class names and overrides summarized.
- Dataset: info/database products exist and point to the same dataset root.
- Budget: GPU count, memory, worker count, disk output, runtime, and checkpoints authorized.

## Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `Batch size should match the number of gpus` | Distributed total batch size is not divisible by GPU count | Use total batch size divisible by world size or omit override |
| NCCL hang | wrong launcher/rank/env/tcp port/GPU visibility | Check `CUDA_VISIBLE_DEVICES`, `--launcher`, ranks, and unique port |
| OOM at first iteration | batch, voxel count, point range, sweeps, image branch, or model too large | Reduce batch, workers, sweeps, point range, or select smaller config |
| `KeyError` in dataset registry | `DATA_CONFIG.DATASET` name not in registry | Use a valid dataset class or add it to `pcdet.datasets.__all__` |
| checkpoint key/shape mismatch | checkpoint was trained with different model/classes/config | Use matching config/checkpoint or load as pretrained with expected omissions |
| evaluation writes no result files | `--save_to_file` not passed or result path misunderstood | Add `--save_to_file` and inspect output `eval/` subtree |
| repeated eval never exits | waiting for new checkpoints | Tune `--max_waiting_mins`, avoid `--eval_all`, or ensure checkpoints arrive |

## Logs to inspect

- Training log under `output/<group>/<tag>/<extra_tag>/train_*.log`.
- Evaluation log under `output/<group>/<tag>/<extra_tag>/eval/**/log_eval_*.txt`.
- TensorBoard subdirectories under the same output tree.

## Command reconstruction

When asked to recover or debug a run, reconstruct the command from:

1. Config path and stem.
2. Output group and `extra_tag`.
3. Batch size / GPU count.
4. `--set` overrides in the log.
5. Checkpoint and eval tag.
6. Launcher and distributed environment.

Use the bundled command planner to reduce transcription errors.
