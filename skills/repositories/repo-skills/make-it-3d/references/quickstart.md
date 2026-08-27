# Make-It-3D Quickstart

This quickstart distills the repo's README and source behavior into an operating recipe. It assumes the user has or will create a Make-It-3D checkout and a CUDA-capable Python environment.

## 1. Prepare Assets

Required or commonly needed assets:

- **Reference image:** a centered foreground object with a meaningful alpha channel. The inspected `main.py` uses `cv2.IMREAD_UNCHANGED`, `cv2.COLOR_BGRA2RGBA`, resizes to `512 x 512`, erodes the alpha mask, and optimizes against the composited object.
- **DPT depth weights:** the main pipeline expects `dpt_weights/dpt_hybrid-midas-501f0c75.pt` relative to the runtime working directory unless the source is edited. DPT utility scripts can accept `--model_weights`.
- **Stable Diffusion weights/cache:** default `--sd_version 2.0` maps to `stabilityai/stable-diffusion-2-base`; `--sd_version 1.5` maps to `runwayml/stable-diffusion-v1-5`; `--hf_key` overrides the model id. Some models require Hugging Face login or token.
- **Optional BLIP2 captioning:** if `--text` is omitted, `main.py` loads `Salesforce/blip2-opt-2.7b` and generates a caption, then edits common background phrases. Provide `--text` to avoid this cost.

## 2. Check the Environment

Run the bundled diagnostic from any directory:

```bash
python /path/to/skill/scripts/make_it_3d_env_check.py --repo-root /path/to/Make-It-3D --dpt-weights /path/to/Make-It-3D/dpt_weights/dpt_hybrid-midas-501f0c75.pt
```

The script reports CUDA status, key Python modules, visible repo files, DPT weights, and common optional export/refine dependencies. Treat missing `tinycudann`, `pytorch3d`, `clip`, `contextual_loss`, `open3d`, `xatlas`, or `nvdiffrast` as workflow-specific action items, not as mysterious import failures.

## 3. Validate Input

```bash
python /path/to/skill/sub-skills/environment-and-inputs/scripts/validate_alpha_input.py --image ref.png
```

A usable image should be RGBA/LA or otherwise expose alpha, have nonzero foreground/background alpha variation, and ideally be centered on one object. If the input is ordinary RGB, create an alpha mask with a segmentation tool before training.

## 4. Build Coarse Commands

```bash
python /path/to/skill/sub-skills/coarse-training/scripts/build_training_commands.py \
  --workspace corgi --ref-path inputs/corgi_alpha.png --text "a corgi dog"
```

The first command optimizes the frontal range (`--phi_range 135 225 --iters 2000`). The second broadens to full 360 degrees (`--phi_range 0 360 --albedo_iters 3500 --iters 5000 --final`). The code stores the workspace under `results/<workspace>`.

## 5. Refine and Export

```bash
python /path/to/skill/sub-skills/refinement-and-export/scripts/build_refine_export_commands.py \
  --workspace corgi --ref-path inputs/corgi_alpha.png --text "a corgi dog" --save-mesh
```

Use the generated commands after the coarse workspace is ready. If refinement appears to train without entering the refine block, include `--final --refine`, because the inspected source nests the refine block inside the final/test branch after training.

## Verification Boundaries

Short checks can validate argument construction, image format, dependency presence, CUDA visibility, and DPT CLI help. Full Make-It-3D quality requires external model downloads, credentials/cache, long CUDA optimization, and sometimes source builds; do not call that verified unless those runs actually completed.
