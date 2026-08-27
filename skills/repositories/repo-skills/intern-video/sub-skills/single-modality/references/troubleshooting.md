# InternVideo2 Single-Modality Troubleshooting

Use the first failing symptom, not the last stack frame, to choose a fix. Most failures fall into dependency, checkpoint, dataset layout, distributed launch, or source-script portability categories.

## Dependency and import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: flash_attn`, `No module named flash_attn.modules.mlp`, or missing `DropoutAddRMSNorm` | The model files import FlashAttention and fused CUDA modules at import time. | Install a FlashAttention version compatible with the local PyTorch/CUDA stack, or use an environment already prepared for the repo. CPU-only environments are insufficient for native model imports. |
| `ImportError` or build errors for Apex / fused ops | CUDA compiler, PyTorch, or extension ABI mismatch. | Rebuild against the exact active PyTorch/CUDA versions. Avoid mixing system CUDA, PyTorch CUDA wheels, and prebuilt extensions from different versions. |
| `Please install DeepSpeed` then process exits | Command includes `--enable_deepspeed` but DeepSpeed is absent. | Install DeepSpeed in the training environment, or remove `--enable_deepspeed` and `--zero_stage` for a non-DeepSpeed debug run. Review batch size and LR scaling after changing launcher. |
| `decord` import error | Video loader dependency missing. | Install Decord and its codec/runtime requirements, or switch only supported raw-frame datasets to `--no_use_decord`. Pretraining multi-source loader requires Decord. |
| `ImportError: petrel_client` warnings or remote-storage failures | Optional object-storage client missing or not configured. | Use local paths, install/configure the storage client, or remove remote URI assumptions from the dataset rows. Do not embed private credentials in commands or skill files. |

## Checkpoint and teacher weight failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `FileNotFoundError` under a placeholder model root or teacher subdirectory | `INTERNVIDEO2_MODEL_PATH` is unset, or required teacher files are absent. | Set `INTERNVIDEO2_MODEL_PATH` or pass explicit checkpoint paths. For pretraining, place InternVL visual encoder under `internvl/internvl_c_13b_224px.pth` and VideoMAEv2-g under `videomae/vit_g_hybrid_1200e_pre.pth` relative to that root, unless the user's code has been patched differently. |
| Distillation fails before loading data due to teacher checkpoint path | The distillation teacher registry in the inspected branch contains non-portable defaults for some teacher files. | Patch or wrap the teacher registry in the user's working tree so `teacher_internvideo2_stage2_1B` and related teachers read from user-provided paths. Confirm the resulting paths before submitting a job. |
| `KeyError` for a teacher name | `--clip_teacher` is not in the registered teacher map for that entry point. | For pretraining use `internvl_clip_6b`; for distillation use one of `teacher_internvideo2_1B`, `teacher_internvideo2_stage2_1B`, or `teacher_internvideo2_6B`. |
| Classifier head shape mismatch | Checkpoint class count differs from `--nb_classes`. | Use the matching dataset checkpoint, pass `--delete_head`, or rely on the K710-to-K400/K600/K700 remapping only for the supported 710-class-head cases. |
| Position embedding shape mismatch or interpolation crash | `num_frames`, `num_segments`, `tubelet_size`, or input size differs from checkpoint assumptions. | Use source model-zoo frame settings first. For linear probing, set `--orig_t_size` to the checkpoint's temporal length. For full finetuning, be cautious because the source code assumes an 8-frame origin in the common path. |
| `No best model`, `No latest model`, or eval loads an unexpected checkpoint | `--output_dir` points at the wrong experiment or lacks expected checkpoint files. | Set `--output_dir` to the experiment directory containing `checkpoint-best.pth` or `checkpoint-latest.pth`, or pass a direct `--finetune`/`--resume` path according to the intended load path. Use a fresh output directory for new training. |

## Dataset and annotation failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Setting file ... doesn't exist` | `--data_path` does not contain the required split CSV. | For finetuning/probing, create `train.csv`, `val.csv`, and `test.csv` under the split root, or point `--data_path` at the directory that already contains them. |
| `Video input format is not correct` | CSV delimiter or column count is wrong. | Match `--split` to the file. Kinetics-style rows need path and label; multi-source pretraining rows need source, path, total time, start time, end time, and target. |
| `Found 0 video clips` | Empty CSV, wrong delimiter, inaccessible paths, or wrong prefix. | Print a few parsed rows, verify path joins with `--prefix`, and confirm that video/frame files are accessible from the worker nodes. |
| Repeated warnings like `video ... not correctly loaded during training` | Decord cannot open the file, codec is unsupported, object storage is unreachable, or frames are missing. | Validate the exact joined path. Try decoding one sample on the same node. For SSV2/HMDB raw-frame layouts, use `--no_use_decord` and verify `filename_tmpl`. |
| `AssertionError` around class count | `--nb_classes` does not match the dataset class expected by the loader. | Use 710 for K710, 400/600/700 for Kinetics variants, 339 for MiT V1, 174 for SSV2/SSV1 source recipes, 101 for UCF101, 51 for HMDB51, and 200 for ANet/HACS source recipes. |
| `NameError` referencing an undefined variable during pretraining video loading | The inspected multi-source pretraining loader contains a portability bug in its object-storage detection branch. | Use local video paths where the branch is not needed, or patch the user's working copy so the check uses the constructed video path variable. Keep the patch minimal and document it in the experiment notes. |

## Distributed launch and DeepSpeed failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Job hangs at distributed initialization | Missing or inconsistent `RANK`, `WORLD_SIZE`, `LOCAL_RANK`, `MASTER_ADDR`, or `MASTER_PORT`; SLURM task count mismatch; firewall/port collision. | For SLURM, keep `--ntasks`, `--ntasks-per-node`, and visible GPUs aligned. For `torchrun`, pass `--nproc_per_node`, `--nnodes`, `--node_rank`, and a reachable master address. Use a unique `MASTER_PORT`. |
| CUDA device index errors | `GPUS_PER_NODE` exceeds visible GPUs or `SLURM_LOCALID` maps incorrectly. | Match `--gres=gpu:<per-node>` to actual GPUs per node and inspect `CUDA_VISIBLE_DEVICES`. |
| DeepSpeed assertion that gradient accumulation does not match `update_freq` | DeepSpeed config generated from args disagrees with runtime command or injected config. | Let the entry point generate its own `deepspeed_config.json`, or keep `gradient_accumulation_steps` equal to `--update_freq`. |
| Rank-local prediction files are missing before merge | Some ranks failed or wrote to a different output directory; single-process run kept `--dist_eval`; barrier aborted. | Check each rank log. Remove `--dist_eval` for local debug. Ensure every rank uses the same `--output_dir` and can write there. |
| Plain `python` command prints `Not using distributed mode` but later hangs or errors | Distributed-only options remained in a non-distributed debug command. | Remove `--enable_deepspeed`, `--dist_eval`, and large multi-GPU assumptions; use a tiny fixture and do not treat it as production validation. |

## Memory and performance failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| CUDA OOM during model creation or first forward | Model scale, frames, per-GPU batch, or unfrozen blocks exceed memory. | Reduce `--batch_size`, `--num_frames`, `--num_segments`, or test crops. Enable `--use_checkpoint` and a suitable `--checkpoint_num`. Prefer S/B/L distilled models for constrained hardware. |
| OOM during eval | Multi-view testing multiplies cost by `test_num_segment * test_num_crop`. | Lower `--test_num_segment` and `--test_num_crop` for smoke tests, then restore model-zoo settings for final metrics. |
| Training is slower than expected | Too many dataloader workers, remote video storage, codec bottlenecks, or excessive CPU contention. | Validate video decode throughput independently, tune `--num_workers`, keep `OMP_NUM_THREADS` conservative, and stage data near the compute nodes. |
| Divergence after changing GPU count | LR is scaled by effective global batch size in code. | Recalculate effective LR after changing `batch_size`, `world_size`, or `num_sample`; lower LR for smaller runs. |

## Source script anomalies to review before reuse

The inspected branch contains several cluster-script quirks that should be corrected in generated or user-reviewed commands rather than copied blindly:

- Some shell `JOB_NAME` values do not match the filename or target dataset/model.
- Some model-zoo/script labels are inconsistent with the Python model registry names.
- At least one linear-probing shell script references an entry point that is not present in the inspected single-modality directory.
- Some 6B probing scripts use older `vit_6B...` model names rather than the registered `internvideo2_6B...` names.
- Pretraining/distillation source shell scripts use bare CSV filenames; prefer explicit user data roots in generated commands.

When in doubt, build a command from the Python entry point and registered model name, not from filename text alone.

## Safe recovery sequence

1. Save the failing command, first error line, launcher environment, model/dataset paths after expansion, and rank log locations.
2. Re-render the command with the bundled helper using the same preset and overrides.
3. Verify files: split CSVs, one sample video/frame directory, model checkpoint, teacher checkpoints, and output directory writability.
4. Remove only the minimum risky option for the next diagnostic run: DeepSpeed, distributed eval, large crops, high batch, or remote data.
5. If a source portability bug is confirmed, patch the user's working copy minimally and record the patch in experiment notes; do not change public skill files or private environment paths.
