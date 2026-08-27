# Training Troubleshooting

Use this reference before retrying expensive training. Prefer the bundled validator and small command checks before launching full CUDA jobs.

## Dataset schema failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` for a paired image from `train_A`, `train_B`, `test_A`, or `test_B` | A prompt JSON key names a file that is missing from one side of the pair. | Run `python sub-skills/training/scripts/validate_training_dataset.py --mode paired --dataset-folder <dataset>`. Make every key in `train_prompts.json` and `test_prompts.json` exist in both matching `A` and `B` directories. |
| Paired training silently ignores images | Extra images exist in `train_A`/`train_B` or `test_A`/`test_B` but are not keyed in the prompt JSON. | Add prompt JSON entries for intended images, or remove extras. The paired loader iterates JSON keys, not directory listings. |
| Captions appear mismatched to images | Prompt JSON keys were copied from one split/domain but filenames differ in the image folders. | Regenerate JSON from the actual paired filenames; keep identical filenames across `A` and `B` for each split. |
| Unpaired loader fails on `fixed_prompt_b.txt` | `fixed_prompt_b.txt` is missing or empty. | Create a non-empty target-domain prompt file. For A→B training/inference, this is the prompt that describes domain B. |
| Unpaired training fails with empty sequence/random-choice errors | `train_A` or `train_B` has no images matched by the source lowercase glob rules. | Put top-level `.jpg`, `.jpeg`, `.png`, `.bmp`, or `.gif` files in both training domains; lowercase extensions are safest. |
| Unpaired FID setup fails or produces invalid statistics | `test_A` or `test_B` has no validation images matched by the source validation glob rules. | Use top-level `.jpg`, `.jpeg`, `.png`, or `.bmp` files in both validation domains. GIFs are not collected for validation. |

## W&B and offline logging

- The documented commands use `--report_to "wandb"` and log image groups through W&B-aware objects.
- If W&B credentials or internet are unavailable, set `WANDB_MODE=offline` before launch and keep the run local. Sync later with W&B tooling if desired.
- If switching to another Accelerate tracker such as TensorBoard, do a short parser/import dry run first; the source code still imports `wandb`, and paired visualization creates W&B image objects before passing logs to Accelerate.
- Use unique `--tracker_project_name` values for separate experiments to avoid mixing dashboards.

## FID, LPIPS, CLIP, and DINO metrics

- Paired training always imports LPIPS and OpenAI CLIP. Validation logs L2, LPIPS, and CLIP-SIM at `--eval_freq` intervals.
- Paired clean-FID is optional. Omit `--track_val_fid` to avoid clean-FID reference feature extraction from `test_B`.
- Unpaired training prepares clean-FID reference features from `test_A` and `test_B` at startup and computes FID/DINO metrics at validation intervals. There is no `--track_val_fid` switch in the unpaired parser.
- The DINO-structure metric uses a CUDA DINO ViT-B/8 extractor through `torch.hub`. If the model is not cached, expect network/cache setup before validation can run.
- To reduce validation cost, increase `--validation_steps` and set a positive `--validation_num_images` for unpaired runs; for paired runs, use `--num_samples_eval` and omit `--track_val_fid` unless FID is needed.

## xformers, CUDA, and memory

| Symptom | Recovery |
| --- | --- |
| Paired error says xformers is unavailable | Remove `--enable_xformers_memory_efficient_attention` or install an xformers build compatible with the active PyTorch/CUDA stack. |
| Unpaired xformers call fails with a lower-level CUDA/PyTorch error | Remove `--enable_xformers_memory_efficient_attention` first. If memory then fails, install a matching xformers build or use smaller batches/checkpointing. |
| CUDA out of memory | Lower `--train_batch_size`, increase `--gradient_accumulation_steps` if effective batch size matters, enable `--gradient_checkpointing`, use `--enable_xformers_memory_efficient_attention` only when compatible, consider paired `--mixed_precision fp16` or `bf16`, and reduce validation image counts. |
| CUDA is not visible | Verify PyTorch sees CUDA before launch. These training scripts instantiate CUDA discriminators/metrics and do not have a verified CPU training substitute. |
| `vision_aided_loss`, `lpips`, `clean-fid`, `clip`, or `diffusers` import errors | Install the repo's training dependency set. The training workflows require more than the lightweight dataset validator. |

## Accelerate process and port issues

- `accelerate config` can persist multi-GPU defaults. If the current run should be single-GPU, pass `--num_processes 1` explicitly.
- If a launch hangs or reports address/port conflicts, choose a free `--main_process_port`, for example `29501`, `29502`, or another unused port.
- Use `CUDA_VISIBLE_DEVICES=<ids>` to limit which GPUs Accelerate can see.
- The documented unpaired recipe sets `NCCL_P2P_DISABLE=1`. Keep it when peer-to-peer/NCCL issues appear, especially on mixed or restricted multi-GPU systems.
- When scaling to multiple GPUs, remember `--train_batch_size` is per process. Adjust gradient accumulation and learning-rate expectations deliberately.

## Training defaults that can surprise users

- Unpaired `--max_train_steps` defaults to `None` in the parser, but the training loop uses it in a range. Set `--max_train_steps` explicitly.
- Pix2Pix-Turbo training expects the documented SD-Turbo base path. Use `--pretrained_model_name_or_path="stabilityai/sd-turbo"` for the source workflow.
- Checkpoints are written when `global_step % checkpointing_steps == 1`, so default names start at `model_1.pkl`, then `model_501.pkl`, `model_1001.pkl`, and so on.
- Full training creates tracker logs, checkpoint files, paired `eval/fid_<step>` folders when FID is enabled, and unpaired `fid_reference_*` plus `fid-<step>/samples_*` folders. Plan storage before long runs.
- The bundled validator does not prove model training will fit in memory; it only proves the filesystem schema expected by the loaders.

## Safe download helper issues

- The bundled downloader requires `--dataset fill50k|horse2zebra`, `--output-dir`, and `--yes`; `--help` is always safe and performs no network action.
- It refuses to overwrite an existing expected dataset directory. Move or remove stale partial data before retrying.
- It requires `unzip` and either `curl` or `wget`.
- If a download is interrupted, remove the partial archive or dataset directory and rerun the helper after confirming network access.
