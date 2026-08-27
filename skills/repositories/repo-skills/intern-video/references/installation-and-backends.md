# Installation and Backend Readiness

## When to read

Read this before promising that an InternVideo command can run. Most repository workflows are research-scale and need external datasets, checkpoints, cluster launchers, and CUDA extension packages.

## Environment families

| Area | Typical Python/dependency surface | Runtime notes |
|---|---|---|
| InternVideo2 single-modality | Python, PyTorch, `decord`, `timm`, `einops`, OpenCV, DeepSpeed, Apex; docs reference UMT-style setup | Full training/finetuning is SLURM + multi-GPU. The 1B/6B scripts use `srun`, DeepSpeed, bf16, and checkpointing. |
| InternVideo2 multi-modality | `pyproject.toml` package `internvideo2_multi_modality`, PyTorch >=2.4.1, `transformers`, `decord`, `av`, `librosa`, `soundfile`, `torchaudio`, DeepSpeed, FlashAttention2 CUDA extensions | Demo/eval often require `PYTHONPATH` rooted at `multi_modality`. Stage2 uses BERT text encoder; CLIP branch may use InternVL/LLM text encoders. |
| InternVideo-Next | PyTorch video training stack, FlashAttention modules, diffusion/JEPA components, dataset loaders | Code is centered around `main_stage1.py` and `main_stage2.py`; full runs need data and GPU memory planning. |
| InternVideo2.5 | Released model/checkpoint documentation with training pointer to external VideoChat-Flash/TPO/HiCo code | Treat as model-selection and paper/release guidance unless the user supplies the external training repo. |
| InternVideo3 inference | `transformers`, `torch`, `qwen-vl-utils`, model weights such as `yanziang/InternVideo3-8B-Instruct` | Use `trust_remote_code=True`; choose FPS and pixel budgets to fit GPU memory. |
| InternVideo3 SFT/eval | XTuner-style package under `InternVideo3_sft`, PyTorch >=2.6, `transformers`, Flash Attention 3, FSDP, benchmark datasets | SFT scripts assume GPUs, metadata JSON, model/processor paths, and often cluster-specific launch wrappers. |

## Required external assets

Always identify these before running or editing commands:

- Dataset root(s): e.g. Kinetics/K710/K400, SSv1/SSv2, HMDB/UCF, WebVid, InternVid, MSRVTT, DiDeMo, ActivityNet, benchmark-specific JSON files.
- Model/checkpoint root(s): e.g. InternVL visual encoder, VideoMAEv2-g teacher, InternVideo2 Stage1/Stage2/CLIP weights, InternVideo3/2.5 Hugging Face model IDs.
- Backend stack: GPU model/VRAM, CUDA toolkit/wheel compatibility, FlashAttention/Apex/DeepSpeed build availability, SLURM partition or torchrun substitute.
- Runtime policy: whether the user authorizes downloads, large training, benchmark evaluation, or job submission.

## Readiness checks

Use the bundled root helper:

```bash
python scripts/check_internvideo_environment.py --json
python scripts/check_internvideo_environment.py --data-root /data/internvideo --model-root /models/internvideo --strict
```

The helper is intentionally conservative: it reports missing optional packages and paths, but it does not install dependencies, download weights, or submit jobs.

## Backend verification boundary for this generated skill

This skill was verified with static/content checks and generated helper execution. Full native InternVideo model jobs were not executed during creation because they require heavyweight prerequisites. When the user asks for a real run, convert the relevant optional backend into a required backend for that downstream task and verify it before submitting work.
