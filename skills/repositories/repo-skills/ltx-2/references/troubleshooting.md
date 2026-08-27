# LTX-2 Cross-Cutting Troubleshooting

## When to read

Read this for install/import, model asset, Gemma, checkpoint-layout, CUDA, or local-path failures that affect more than one sub-skill. Workflow-specific failures live in each sub-skill's own `references/troubleshooting.md`.

## Quick diagnosis order

1. Run the root environment checker:

   ```bash
   python path/to/ltx-2/scripts/check_ltx2_environment.py --json
   ```

2. Confirm the task route in the root `SKILL.md`.
3. Confirm model layout in `model-assets.md`.
4. If a command is heavy, first use the relevant bundled command builder or validator.
5. Only run generation, preprocessing, training, downloads, external uploads, or kernel builds after explicit user approval.

## Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named 'ltx_core'`, `ltx_pipelines`, or `ltx_trainer` | Packages are not installed in the active Python environment. | Install or sync the LTX packages, then rerun `check_ltx2_environment.py`. Use the Python executable that will run the workflow. |
| CLI or config says a model path does not exist | LTX expects local filesystem paths, not Hugging Face URLs. | Download or point to local files after user approval. Keep split component paths distinct. |
| Split transformer complains that no VAE is present | A split LTX-2.5 transformer file was used without `video_vae_path` and/or `audio_vae_path`. | Add the VAE component paths needed by the workflow. Video-only tasks may not need the audio VAE; audio workflows do. |
| Gemma version mismatch or bad text-encoder output | Checkpoint and text encoder are from different model families. | Use the checkpoint's matching Gemma assets: LTX-2.5 packed LTX-specific Gemma 4, or legacy matching Gemma directory. Regenerate precomputed text embeddings after switching. |
| `frames must satisfy ...` or resolution alignment errors | Frame count or dimensions do not match VAE factors. | Use frame counts such as 1, 9, 17, 25, 49, 89, 97, 121 for default `T=8`; use width/height multiples of the VAE spatial factor, commonly 32. |
| CUDA is unavailable even though a GPU exists | CPU-only torch, incompatible driver/wheel, container GPU passthrough missing, or wrong environment. | Use `performance-backends/scripts/check_backend_readiness.py`; reinstall a compatible CUDA framework only after confirming package/driver constraints. |
| Out-of-memory during generation or validation | Resolution, frames, model size, VAE decode mode, or batch size exceeds VRAM. | Consider `--offload cpu`, `--offload disk`, `--quantization fp8-cast`, fewer frames, smaller resolution, lower batch, DiffVAE tiling, or route to `performance-backends`. |
| Optional accelerator import fails (`ltx_kernels`, `natten`, FlashAttention) | Optional backend not installed, wrong architecture, missing build tools, or unsupported GPU. | Treat as optional unless the user explicitly needs that backend. Read `performance-backends`; do not claim the accelerator is verified. |
| Hugging Face download returns 401/403 | Gated repo terms not accepted or token lacks read scope. | Ask the user to accept terms and provide a proper read-authenticated download context. Do not embed tokens in commands or logs. |
| Training uses stale precomputed data after a version switch | `.precomputed/conditions` and latents were produced with old model/Gemma/buckets/trigger. | Use a fresh output directory or `--overwrite` after user approval. Route to `data-preparation`. |

## Public/private boundary

Generated skill references are safe to share. Do not copy private environment prefixes, local cache paths, API keys, or token-bearing commands into runtime notes. If troubleshooting requires host-specific details, keep them in a separate private report or working notes.
