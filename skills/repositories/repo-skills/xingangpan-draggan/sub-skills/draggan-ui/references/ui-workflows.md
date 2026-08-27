# DragGAN UI Workflows

## Desktop visualizer

Use the bundled `launch_draggan_gui.py` helper to discover local `.pkl` files and print a launch command. It replaces the repo’s brittle hard-coded shell/batch checkpoint list.

```bash
python sub-skills/draggan-ui/scripts/launch_draggan_gui.py \
  --repo-root /path/to/DragGAN \
  --checkpoint-dir /path/to/checkpoints \
  --capture-dir captures
```

Review the output, then add `--execute` to launch. `--browse-dir` configures the GUI’s model browser. A checkpoint may also be passed explicitly with repeated `--pkl` options. URLs are accepted by the underlying visualizer, but network access and model caching should be deliberate.

The desktop UI groups controls into Network & latent, Drag, and Capture. Load a model, select a seed, place a source point followed by its target, and start the drag. Reset points when a pair is incomplete. Use flexible/fixed masks for locality and reset the mask when changing models or seeds.

## Gradio demo

Use the Gradio helper for a browser/headless-friendly route:

```bash
python sub-skills/draggan-ui/scripts/launch_gradio_demo.py \
  --repo-root /path/to/DragGAN \
  --cache-dir checkpoints \
  --listen
```

The helper refuses to start if the cache directory has no `.pkl` files. `--listen` binds the source app to `0.0.0.0`; `--share` asks Gradio for a share link and should only be used when the user understands the network exposure.

The Gradio controls expose model, seed, step size, latent space (`w`/`w+`), motion lambda, point reset, mask editing, mask reset/show, and start/stop. Changing model, seed, or latent space reinitializes the image and clears the edit state.

## Renderer facts

The verified renderer surface includes:

- `Renderer(disable_timing=False)`; the Gradio app uses a timing-disabled renderer.
- `init_network(res, pkl, w0_seed, w_load, w_plus, noise_mode, trunc_psi, trunc_cutoff, input_transform, lr)`.
- `_render_drag_impl(res, points, targets, mask, lambda_mask, reg, feature_idx, r1, r2, random_seed, noise_mode, trunc_psi, force_fp32, layer_name, sel_channels, base_channel, img_scale_db, img_normalize, untransform, is_drag, reset, to_pil)`.
- The renderer selects the generator implementation from filename signals (`stylegan2`, `stylegan3`, or `stylegan_human`) and adds an `AI Generated` watermark to displayed images.

## Output and safety

Captures are image frames, not latent checkpoints. Keep source model files and generated outputs outside the skill directory. Do not remove the watermark or expose a Gradio server without an explicit user request.
