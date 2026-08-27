# Cross-Cutting Troubleshooting

Read this before running long GPU jobs or when the error does not clearly belong to one sub-skill.

## Route by symptom

| Symptom or error signal | Likely cause | Next step |
| --- | --- | --- |
| ``models_root not exists`` | `--model-base` points to a missing checkpoint root. | Run `sub-skills/checkpoint-and-setup/scripts/validate_checkpoint_layout.py --model-base <path>`. |
| `VAE checkpoint not found` | Missing `hunyuan-video-t2v-720p/vae/pytorch_model.pt`. | Read `sub-skills/checkpoint-and-setup/references/checkpoint-layout.md`. |
| `Invalid fp8_map path` | FP8 checkpoint exists without the companion `_map.pt` file. | Read `sub-skills/parallel-and-optimization/references/parallel-and-fp8.md`. |
| `Latent channels (...) must match the VAE channels` | `--latent-channels` conflicts with `--vae`. | Use default `--latent-channels 16` with `884-16c-hy`. |
| Video length error mentioning multiple of 4 | Default 3D VAE needs `video_length = 4n + 1`. | Use 65 or 129 frames, or another valid value. |
| `Ulysses Attention and Ring Attention requires xfuser package` | Multi-GPU path selected without `xfuser`. | Install xDiT dependency or use single-GPU mode. |
| world size mismatch | `--nproc_per_node` does not equal `--ulysses-degree * --ring-degree`. | Use `parallel-and-optimization/scripts/build_optimized_command.py multi-gpu`. |
| floating point exception/core dump | CUDA/CUBLAS/CUDNN/PyTorch binary mismatch on specific GPUs. | Use README-backed CUDA 12.4 CUBLAS/CUDNN stack or force CUDA 11.8 wheel path. |
| OOM on 40GB/48GB GPU | Single-GPU generation exceeds README memory floor. | Lower resolution, use CPU offload, FP8, or multi-GPU xDiT if dependencies/checkpoints are ready. |
| Gradio reachable from other machines unexpectedly | Default server bind may use `0.0.0.0`. | Use `web-demo/scripts/build_gradio_command.py --server-name 127.0.0.1`. |

## Safe preflight sequence

1. Check dependencies and CUDA visibility:

```bash
python scripts/check_hunyuan_video_env.py --check-optional
```

2. Check checkpoint layout without loading weights:

```bash
python sub-skills/checkpoint-and-setup/scripts/validate_checkpoint_layout.py --model-base ckpts
```

3. Build the intended command without launching sampling:

```bash
python sub-skills/inference/scripts/build_sample_command.py --prompt "A cat walks on the grass, realistic style." --height 544 --width 960 --video-length 129 --use-cpu-offload
```

Only after these pass should a future agent run the generated sampling command in a suitable HunyuanVideo environment.
