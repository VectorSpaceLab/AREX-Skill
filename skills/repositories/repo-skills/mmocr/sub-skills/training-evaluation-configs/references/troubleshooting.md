# Training, evaluation, and config troubleshooting

Use this page after a config smoke fails or before launching an expensive train/test job.

## Fast triage

1. Run [`../scripts/mmocr_config_smoke.py`](../scripts/mmocr_config_smoke.py) with the exact config and overrides.
2. Check `default_scope`, `model.type`, dataloader dataset types, evaluator metric types, and `has_tta`.
3. Verify caller-provided dataset and checkpoint paths before launching.
4. Decide whether CPU/debug, one-GPU, distributed, or Slurm execution is actually required.
5. Stop before network downloads, long training, or cluster jobs unless the user approved those resources.

## Config load and override failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `FileNotFoundError` while loading `_base_` | Config inherits a relative base that is not present beside the caller's config | Use a complete config bundle, install MMOCR with its packaged configs, or rewrite the config so inherited files are present. |
| Error about duplicate variable names in bases | Two inherited base files define the same top-level symbol | Remove one base or rename/inline the conflicting value. |
| `default_scope` is missing or not `mmocr` | Custom config copied from another OpenMMLab repo | Add `default_scope = 'mmocr'` or explicitly initialize the MMOCR registry scope in the runtime. |
| `--cfg-options` token rejected | Token is not `key=value` or shell split a list/tuple | Quote the whole override: `'train_cfg.max_epochs=1'`, `'pipeline=[...]'`. |
| Override appears ignored | Wrong dotted key or override is applied to a copy rather than the referenced object | Inspect the smoke helper JSON before launch and update the config file if the edit is structural. |

## Data and checkpoint mismatches

| Symptom | Likely cause | Recovery |
|---|---|---|
| Dataset path or annotation file missing | `data_root`, `data_prefix`, or `ann_file` points to caller-invalid paths | Use `data-preparation` to validate the layout, then update the config or override data fields. |
| LMDB recognition data fails in a normal image pipeline | LMDB config requires an ndarray loader and LMDB dataset type | Use the LMDB-specific generated config pattern and route to `data-preparation` for loader checks. |
| Test job cannot find checkpoint | `CHECKPOINT` is missing, mistyped, or refers to an unavailable remote artifact | Provide a local checkpoint, allow intentional download, or choose a model/checkpoint from the same family. |
| Checkpoint loads with missing/unexpected keys | Config family does not match checkpoint family or number of classes/dictionary differs | Match task + family + dictionary + head settings before testing. |
| KIE metrics look wrong | WildReceipt-style labels/classes or relation fields do not match the config | Check KIE schema and class mapping in `data-preparation` before rerunning evaluation. |

## Work directory, resume, and checkpoint semantics

| Symptom | Likely cause | Recovery |
|---|---|---|
| User wants to test a checkpoint but set `resume=True` | Resume is training-state recovery, not evaluation checkpoint selection | For testing, pass `CHECKPOINT` to the test launcher. For fine-tuning initialization, use `load_from`; for continuing training, use `--resume`. |
| Resume starts the wrong run | `WORK_DIR` points to an old experiment | Use a new work directory or cleanly identify the intended latest checkpoint. |
| Logs/checkpoints appear in an unexpected directory | `work_dir` in config and command option disagree | Prefer an explicit `--work-dir WORK_DIR` in the command and confirm the smoke summary. |

## CPU, CUDA, AMP, and distributed failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| CPU debug run is requested | Training docs allow CPU-only runs but they are slow | Set `CUDA_VISIBLE_DEVICES=-1`, shorten epochs, and use tiny/debug data before full training. |
| CUDA unavailable despite GPUs | CPU-only torch/MMCV build, container lacks GPU passthrough, or driver/wheel mismatch | Verify `torch.cuda.is_available()`, torch CUDA version, and the MMEngine/MMCV build before launching. |
| `--amp` fails or loss becomes invalid | Family or operator does not support mixed precision | Check [`model-zoo.md`](model-zoo.md); disable AMP for unverified or unsupported families. |
| Distributed launch hangs | Rendezvous port conflict, wrong GPU count, NCCL issue, or multi-node env missing | Choose a unique `PORT`, match `--gpus` to visible devices, and verify distributed environment before retrying. |
| Slurm command fails immediately | Not inside a Slurm allocation or required variables/partition are invalid | Ask for site policy, partition, allocation, `srun` availability, and resource limits before constructing the job. |

CPU-debug command shape:

```bash
CUDA_VISIBLE_DEVICES=-1 mim train mmocr CONFIG --work-dir WORK_DIR \
  --cfg-options train_cfg.max_epochs=1 train_cfg.val_interval=1
```

## TTA, prediction saving, and visualization

| Symptom | Likely cause | Recovery |
|---|---|---|
| `--tta` fails | Config lacks both `tta_pipeline` and `tta_model`, or task is not a supported recognition TTA route | Confirm `has_tta=true` with the smoke helper; otherwise do not enable TTA. |
| No visual window on remote server | GUI display is unavailable | Use `--show-dir VIS_DIR` instead of interactive display. |
| Saved predictions are hard to locate | Work directory/timestamp conventions hide artifacts | Set an explicit `WORK_DIR` and inspect the generated output tree after the run. |

## When to route elsewhere

- Annotation, dataset-zoo, LMDB, or image-layout issue: [`data-preparation`](../../data-preparation/SKILL.md).
- Image/folder OCR prediction issue: [`ocr-inference`](../../ocr-inference/SKILL.md).
- Registry/custom component/DataSample issue: [`model-api-components`](../../model-api-components/SKILL.md).
