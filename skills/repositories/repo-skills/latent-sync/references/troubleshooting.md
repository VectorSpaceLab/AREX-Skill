# LatentSync troubleshooting

Use this before rerunning an expensive job. Most LatentSync failures are path, checkpoint, backend, or temp-dir problems that can be detected early with `scripts/check_env.py`.

## First-line preflight

```bash
python scripts/check_env.py --check-imports --check-cuda --check-ffmpeg
```

Add these only when relevant:

- `--check-scenedetect` for raw-video preprocessing.
- `--check-assets` for the bundled demo inputs and mask/image smoke path.
- `--strict-versions` when you want to compare the environment against the verified baseline in this skill.

## Verified baseline

This skill was distilled against a working inspection environment with:

- Python `3.10.13`
- `torch 2.5.1+cu121`
- `torchvision 0.20.1+cu121`
- `diffusers 0.32.2`
- `transformers 4.48.0`
- `decord 0.6.0`
- `mediapipe 0.10.11`
- `insightface 0.7.3`
- `onnxruntime-gpu 1.21.0`
- `gradio 5.24.0`
- `numpy 1.26.4`
- `setuptools 80.9.0`
- `ffmpeg 8.0.1`

CUDA allocation on 8× NVIDIA A100-SXM4-40GB succeeded in that environment.

## Cross-cutting blockers

| Symptom | Likely cause | First action |
| --- | --- | --- |
| `ModuleNotFoundError: latentsync` / `scripts` / `preprocess` / `eval` | The helper was launched from outside the LatentSync runtime tree, or `--repo-root` was omitted | Pass `--repo-root` explicitly; the repo has no packaging metadata, so helpers add the checkout to `sys.path` themselves. |
| `ffmpeg not found` | `ffmpeg` is missing from `PATH` | Install or expose `ffmpeg` before inference, preprocessing, or evaluation. |
| `scenedetect not found` | PySceneDetect CLI or import is missing | Install/expose the `scenedetect` package and binary before raw-video preprocessing. |
| `torch.cuda.is_available() == False` | CPU-only build or hidden GPU | Core inference, preprocessing, and training require CUDA; do not treat a CPU import as a substitute. |
| `pkg_resources` or setuptools import errors | Broken `setuptools` baseline | Restore a compatible `setuptools` version; the verified baseline used `80.9.0`. |
| `onnxruntime` provider or CUDA execution errors | Wrong ONNX Runtime build or unavailable GPU provider | Use `onnxruntime-gpu` and confirm the CUDA provider is visible. |
| `gradio_app` import emits a network/version check | Harmless package version probe during import | Ignore the warning unless the import itself fails. |
| Missing checkpoint file | Prerequisite asset not present | Stop and name the missing file before launching a long workflow. |

## Inference failures

### Missing U-Net or Whisper checkpoint

Symptoms:

- `U-Net checkpoint not found` from `scripts/run_inference.py`.
- `torch.load` fails for `checkpoints/latentsync_unet.pt`.
- The run starts but produces poor-looking output after mixing the wrong checkpoint and config family.

Recovery:

1. Use `configs/unet/stage2_512.yaml` for the released v1.6 512 workflow or `configs/unet/stage2.yaml` for the 256/v1.5 workflow.
2. Confirm the Whisper checkpoint matches `model.cross_attention_dim`.
3. Verify `configs/scheduler_config.json` and `latentsync/utils/mask.png` exist in the runtime tree.
4. If the task is to choose a checkpoint or train a new one, route to the training sub-skill.

### Path-sensitive video/audio errors

Symptoms:

- `ffmpeg` muxing fails late in the run.
- Media files exist, but the wrapper rejects them before the pipeline starts.

Recovery:

- Use simple paths without spaces or shell metacharacters.
- Keep `--temp-dir` disposable because the pipeline deletes and recreates it.
- Run `scripts/run_inference.py --preflight-only` before a long GPU job.

### DeepCache or UI launch issues

Symptoms:

- Missing DeepCache import.
- The Gradio app opens a browser or public share unexpectedly.

Recovery:

- Use the bundled launcher for explicit `--share/--no-share` and `--browser/--no-browser` control.
- Do not expect `--enable-deepcache` to hide a missing dependency import.

## Data-preparation failures

### Missing auxiliary checkpoints

Required files:

- `checkpoints/auxiliary/syncnet_v2.model`
- `checkpoints/auxiliary/sfd_face.pth`
- `checkpoints/auxiliary/koniq_pretrained.pkl`

Recovery:

- Confirm the files are present before GPU stages start.
- Keep the first stage on a disposable raw tree because broken-video pruning is destructive.
- If the visual-quality stage fails while building its backbone, check the cached ResNet-50 weights as well.

### Missing `scenedetect` or `ffmpeg`

Symptoms:

- The preflight checker reports the binary is missing.
- Shot detection or resampling fails immediately.

Recovery:

- Install/expose both the `scenedetect` package and the `ffmpeg` binary before the pipeline starts.
- Use `scripts/check_env.py --check-scenedetect --check-ffmpeg` to verify both the binary and import path.

### No face detected or temp-dir collisions

Symptoms:

- Alignment skips many clips.
- `sync_av` or `filter_visual_quality` fails deep in a worker process.
- Reruns behave unpredictably because stale scratch files remain.

Recovery:

- Start with a tiny single-face clip and `--per-gpu-num-workers 1`.
- Use a run-specific scratch directory on fast local disk.
- Resume with `--start-at <stage>` only after the upstream sibling directories are complete.

## Training failures

### Malformed or empty fileslist

Symptoms:

- The dataloader loops on bad rows.
- `ValueError: data_dir and fileslist cannot be both empty`.
- The launcher fails late instead of naming the broken line.

Recovery:

- Regenerate the list with the bundled fileslist helper.
- Run the launcher with `--preflight` before `--execute`.
- Prefer explicit fileslists for U-Net; the directory fallback scans only top-level `.mp4` files.

### DDP / `torchrun` launch problems

Symptoms:

- `KeyError: 'RANK'`
- NCCL initialization fails before the dataloader starts.
- A direct `python` launch behaves differently from `torchrun`.

Recovery:

- Use `torchrun -m scripts.train_unet ...` or `torchrun -m scripts.train_syncnet ...` through the bundled launcher.
- Keep `--nproc_per_node` at or below the number of visible GPUs.
- Select GPUs with `CUDA_VISIBLE_DEVICES`, not with config edits.

### VRAM or checkpoint mismatch

Symptoms:

- CUDA OOM on stage 2 or 512px configs.
- Missing or unexpected keys while loading a checkpoint.
- A stage looks like it started but too many layers were silently reinitialized.

Recovery:

- Treat `stage2_512.yaml` as a high-VRAM configuration, not a smoke target.
- Keep the config family aligned with the checkpoint family.
- Check `cross_attention_dim`, `resolution`, and `num_frames` before assuming a checkpoint is wrong.

## Evaluation failures

### No face detected or too little video

Symptoms:

- SyncNet confidence reports no crop videos.
- FVD fails on frames 20:36.

Recovery:

- Use a clip with a visible, sufficiently large face.
- For SyncNet confidence, run with `--keep-temp` if you need to inspect detector crops.
- For FVD, use clips with at least 36 frames and multiple videos per side when you want a meaningful score.

### Missing metric checkpoints

Required files:

- `checkpoints/auxiliary/syncnet_v2.model`
- `checkpoints/auxiliary/sfd_face.pth`
- `checkpoints/auxiliary/i3d_torchscript.pt`
- `checkpoints/auxiliary/koniq_pretrained.pkl` for preprocessing-quality references
- `checkpoints/stable_syncnet.pt` when evaluating a SyncNet checkpoint

Recovery:

- Stop at preflight and fix the missing file instead of chasing a downstream traceback.
- Use the evaluation sub-skill only after candidate videos or validation data already exist.

## When to stop

Stop and report a prerequisite when:

- A required checkpoint is missing.
- A required backend is unavailable.
- A directory is empty or malformed.
- A workflow wants generation, training, or preprocessing rather than evaluation.

Route the problem to the owning sub-skill once the blocker is identified.
