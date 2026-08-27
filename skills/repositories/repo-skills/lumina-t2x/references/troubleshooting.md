# Troubleshooting

## Purpose

Use this page for cross-cutting Lumina-T2X failures that affect more than one subskill.

## FlashAttention import failures

**Symptoms**
- `ModuleNotFoundError: No module named 'flash_attn'`
- Importing `lumina_t2i`, `lumina_next_t2i`, `lumina_audio`, `lumina_music`, `visual_anagrams`, or the ImageNet benchmark model modules fails before the CLI can start.

**Likely causes**
- `flash-attn` was never installed.
- The installed build does not match the local CUDA/PyTorch stack.
- The machine lacks `nvcc` or a compatible prebuilt wheel for the selected environment.

**Recovery**
- Install a compatible CUDA-enabled FlashAttention build before retrying image, audio/music, visual-anagram, or ImageNet workflows.
- Re-run `scripts/check_env.py --workflow image` or the relevant subskill checker after installation.
- If you only need image-training notes or a non-runtime workflow review, keep the limitation explicit; do not claim the environment is ready for image inference.

## Visual anagram animation dependencies

**Symptoms**
- `ModuleNotFoundError: No module named 'imageio'`
- Importing `visual_anagrams.animate` fails even though the view helpers exist.

**Likely causes**
- `imageio` or `imageio-ffmpeg` was not installed from the visual-anagrams dependency set.
- The environment has the view package but not the animation stack.

**Recovery**
- Install the visual-anagrams dependencies from the branch environment file before retrying animation.
- Re-run `scripts/check_env.py --workflow visual-anagrams` or the bundled `check_views.py` helper after installation.

## PyTorch / MKL mismatch

**Symptoms**
- `ImportError: ... libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent`
- Torch loads but emits MKL / NumPy warnings on import.

**Likely causes**
- MKL and Intel OpenMP versions do not match the PyTorch build.
- The environment pulled in a NumPy 2.x build that is incompatible with the selected PyTorch wheel.

**Recovery**
- Use a fresh private inspection environment instead of mutating a user-owned one.
- Prefer a PyTorch + NumPy combination that matches the repo's CUDA wheel family and then reinstall the repo dependencies.
- Re-run `scripts/check_env.py` after the repair.

## Apex issues

**Symptoms**
- `No module named 'fused_layer_norm_cuda'`
- Apex imports succeed, but training or inference crashes on fused norms.

**Likely causes**
- Apex was installed as a Python-only build.

**Recovery**
- Uninstall the broken Apex build or replace it with a full CUDA+C++ build.
- If Apex is not needed for the selected workflow, leave it out entirely.

## CUDA / distributed startup failures

**Symptoms**
- `nccl` initialization errors.
- `torch.cuda.is_available()` is false.
- Single-GPU inference scripts fail when `--num_gpus` is not 1.

**Likely causes**
- The runtime cannot see a CUDA device or the user selected an unsupported GPU count.
- The script was started with the wrong launch mode for its backend.

**Recovery**
- Verify the GPU is visible and the environment sees CUDA.
- Use the subskill-specific launch instructions exactly; several inference paths are single-GPU only.
- For training, follow the `torchrun` or Slurm guidance in the training subskills.

## Hugging Face checkpoint and token problems

**Symptoms**
- Checkpoint download fails.
- The script warns about a gated model or a missing token.
- `model_args.pth` or `consolidated*.pth/.safetensors` is missing from the checkpoint directory.

**Likely causes**
- The checkpoint folder is incomplete or from the wrong model family.
- A gated model requires an access token.

**Recovery**
- Validate the checkpoint layout with the relevant subskill checker before launching inference.
- Use the matching model family for the chosen script (`lumina`, `lumina_next`, audio/music, or ImageNet benchmark).
- Re-download or reconvert the checkpoint if the layout is wrong.

## Audio / music specific issues

**Symptoms**
- `soundfile`, `openai`, `omegaconf`, `torchdyn`, or `torchlibrosa` import failures.
- The audio demo cannot build structure captions.
- The demo complains about `sample_rate` or checkpoint subdirectories.

**Likely causes**
- The audio/music extras were not installed.
- The OpenAI API key or proxy base URL was not configured for structure caption generation.
- The checkpoint folder is missing `audio_generation`, `music_generation`, `maa2`, or `bigvnat`.

**Recovery**
- Use the audio-music subskill checker and fix the checkpoint tree or config file before rerunning.
- If the structure-caption helper needs network or credentials, treat that as an explicit external dependency rather than a silent repo bug.

## ImageNet training issues

**Symptoms**
- `torchrun` / Slurm launch fails.
- The script cannot find the ImageNet train/val folder structure.
- The job requests too few GPUs for the selected model size.

**Likely causes**
- The ImageNet folder layout is wrong.
- The selected `exps/*.sh` file was not edited for the local path.
- The model size requires a larger cluster than the current hardware.

**Recovery**
- Validate the dataset layout with the ImageNet training subskill checker.
- Confirm the shell script points at the local train root before launching.
- For larger models, follow the repo's Slurm guidance instead of a single-node run.
