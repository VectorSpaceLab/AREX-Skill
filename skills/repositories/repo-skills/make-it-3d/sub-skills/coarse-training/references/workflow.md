# Coarse Training Workflow

## Purpose

The coarse stage optimizes a NeRF from one alpha-masked reference image. The README recommends a progressive camera strategy: start near the frontal reference view, then expand to full 360 degrees.

## Phase 1: Frontal Optimization

README-backed command:

```bash
python main.py --workspace NAME --ref_path REF_ALPHA.png --phi_range 135 225 --iters 2000 --text "object prompt"
```

What happens in source:

- `main.py` rewrites `opt.workspace` to `results/<workspace>` and creates the directory.
- It loads `DPTDepthModel` from `dpt_weights/dpt_hybrid-midas-501f0c75.pt`.
- It loads Stable Diffusion by default (`--guidance stable-diffusion`) or CLIP if selected.
- It reads and masks the alpha reference image, predicts DPT depth, creates `NeRFDataset` train/val loaders, and calls `Trainer.train(...)`.
- It forces `opt.cuda_ray = True` after parsing arguments.

## Phase 2: Full 360-Degree Optimization

README-backed command:

```bash
python main.py --workspace NAME --ref_path REF_ALPHA.png --phi_range 0 360 --albedo_iters 3500 --iters 5000 --final --text "object prompt"
```

`--final` adds a test-render pass after training. If the user wants a back-view prompt, add `--need_back`.

## Prompt Guidance Choices

| Flag | Behavior |
| --- | --- |
| `--guidance stable-diffusion` | Default; uses Stable Diffusion 2.0 unless `--sd_version 1.5` or `--hf_key` is supplied. |
| `--guidance clip` | Uses OpenAI CLIP guidance path; can avoid Stable Diffusion model load but still needs OpenAI CLIP. |
| `--text "..."` | Avoids BLIP2 caption generation and improves reproducibility. |
| omit `--text` | Loads BLIP2 and generates a caption from the image. |
| `--negative "..."` | Negative prompt passed into text embedding paths. |
| `--need_back` | Adds a back-view prompt with `face` as part of negative text for back-view conditioning. |

## Outputs to Expect

Workspace is under `results/NAME` because `main.py` prepends `results/` to `--workspace`.

Common generated items include:

- `setting.txt` with parsed options.
- `checkpoints/` with model checkpoints from `Trainer`.
- `train/` and validation/test render outputs from `Trainer`.
- DPT depth PNGs named from the text prompt.
- Logs such as `log_df.txt` inside the workspace.

Do not assume every output exists after a failed or interrupted run. Check the log and checkpoint directory before resuming.
