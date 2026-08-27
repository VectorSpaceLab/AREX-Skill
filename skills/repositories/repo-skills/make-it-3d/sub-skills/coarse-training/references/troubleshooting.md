# Coarse Training Troubleshooting

## Long or stretched geometry

Evidence: README explicitly recommends increasing reference FOV and related settings.

Try the frontal phase with:

```bash
python main.py --workspace NAME --ref_path REF_ALPHA.png --phi_range 135 225 --iters 2000 --fov 60 --fovy_range 50 70 --blob_radius 0.2 --text "object prompt"
```

Also check alpha mask quality. A large opaque background region can encourage elongated geometry.

## Out-of-memory during training

Actions:

- Use `--w` and `--h` below the default `128` only as a last resort because quality may drop.
- Reduce `--max_ray_batch` for inference/test memory pressure.
- Try `--fp16` if the installed torch/CUDA stack supports it.
- Avoid BLIP2 captioning by passing `--text`.
- Close other GPU jobs and verify memory with `nvidia-smi`.

## Default backbone fails

The default `--backbone tcnn` requires `tinycudann`. If unavailable, emit `--backbone vanilla` only after explaining that it may be slower and still requires raymarching CUDA because the source sets `opt.cuda_ray = True`.

## Stable Diffusion model load fails

If `--guidance stable-diffusion` fails due model access or cache, verify Hugging Face login/token/cache. If the user accepts a different objective, `--guidance clip` switches to CLIP guidance, but it changes the optimization behavior and still needs OpenAI CLIP.

## Training resumes unexpectedly or overwrites

`--ckpt latest` is the default. If `results/NAME/checkpoints` exists, the Trainer attempts to load latest checkpoint. Use a new workspace for a fresh run or set `--ckpt scratch` if the source path accepts that behavior.

## DPT depth looks wrong

Make-It-3D normalizes predicted depth after masking. Bad alpha masks, missing foreground, or a poor DPT estimate can propagate into geometry. Validate the alpha image, inspect generated depth PNGs in the workspace, and consider a cleaner crop/mask.
