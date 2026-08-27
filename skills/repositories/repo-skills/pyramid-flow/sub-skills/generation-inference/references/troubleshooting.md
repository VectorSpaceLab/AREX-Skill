# Generation Troubleshooting

Use the checker script first when a generation workflow fails.

```bash
python scripts/check_generation_prereqs.py --help
```

## Fast symptom table

| Symptom | Likely cause | Fast check | Recovery |
| --- | --- | --- | --- |
| Missing checkpoint path | The wrapper was launched without a valid checkpoint directory. | Verify the model path exists and contains the variant subdirectory. | Pass the correct checkpoint root or pre-download the model bundle. |
| Wrong model repository | The checkpoint family does not match the requested model name. | Compare `pyramid_flux` vs `pyramid_mmdit`. | Use the checkpoint family that matches the request and the variant. |
| `pyramid_flux` + 768p fails fast | The bundled launcher intentionally rejects this incompatible pair. | Check the model name and resolution. | Switch to `pyramid_mmdit` for 768p or downgrade to 384p. |
| 384p / 768p mismatch | The requested resolution does not match the chosen variant. | Compare `resolution` with the selected variant. | Use `diffusion_transformer_384p` for 384p and `diffusion_transformer_768p` for 768p. |
| CUDA OOM | The model is too large for the current GPU memory budget. | Check whether CPU offload is enabled in the single-GPU path. | Use `cpu_offloading=True` or `model.enable_sequential_cpu_offload()` for single-GPU runs; for multi-GPU, reduce batch pressure or use more GPUs. |
| `world_size` vs `sp_group_size` mismatch | The torchrun count does not match the sequence-parallel group size. | Compare `--nproc_per_node` with `--sp_group_size`. | Relaunch with the same number for both values. |
| Missing `image_path` for image-to-video | The image-to-video command was launched without an input image. | Check the parsed arguments before launch. | Supply a readable image path and make sure it points to an actual image file. |
| Gradio or Hugging Face download failure | Cache permission, network, or repository access problem. | Retry the download manually and verify the cache directory. | Reuse a local checkpoint cache or pre-download the model with `snapshot_download`. |
| No output video | Output file path was never written or rank 0 never completed. | Check the rank 0 log and the requested output path. | Write to a writable location and confirm the process completed successfully. |

## Required failure cases

### 1. `pyramid_flux` with a 768p variant

This should fail before launch with a clear compatibility explanation.

Recommended message shape:

> `pyramid_flux` does not support the requested 768p path in the bundled launcher. Use `pyramid_mmdit` for 768p, or switch to the 384p path.

### 2. Image-to-video without `image_path`

This should be rejected before the model is loaded.

Recommended message shape:

> `image_path` is required for image-to-video. Provide a readable image file before launching.

## Memory and offload guidance

- Single-GPU runs can use `cpu_offloading=True` to reduce memory use.
- For the smallest memory footprint, call `model.enable_sequential_cpu_offload()` before generation.
- The multi-GPU sequence-parallel path in the repo uses `cpu_offloading=False`; it is not a CPU-offload fallback.
- If the checkpoint still does not fit, reduce resolution, use fewer frames, or add GPUs.

## Multi-GPU launch checks

Before running a distributed generation job, confirm all of the following:

1. CUDA is visible to PyTorch.
2. The GPU count is at least the requested `sp_group_size`.
3. `torchrun --nproc_per_node` matches `sp_group_size`.
4. The chosen model name and resolution are compatible.
5. The checkpoint path exists and contains the expected variant subdirectory.

## Cache and download fixes

- If the Gradio demo fails while downloading, retry with a writable cache location.
- If the cache was populated by a broken download, remove the broken model directory and download again.
- If the repository is behind a proxy, prefer a pre-downloaded local checkpoint path over live download.

## MPS-specific caveat

The README mentions an MPS path, but the bundled launchers and notebook recipes remain CUDA-oriented. If you are adapting the workflow for Apple Silicon, expect to replace `torch.cuda` placement calls and avoid the multi-GPU launcher path.
