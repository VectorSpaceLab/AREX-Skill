# Inference Workflows

Use these workflows to answer practical Gradio app requests while preserving the distinction between safe static inspection and actual inference launch.

## Choose An App

1. Identify the user's control intent:
   - Crisp object edges or threshold experimentation: Canny.
   - Straight lines, rooms, buildings, or perspective guides: M-LSD/Hough.
   - Soft boundaries, recoloring, or stylization while preserving many details: HED.
   - Human-drawn sparse controls: scribble or interactive scribble.
   - Automatically synthesized sketch-like controls: fake scribble.
   - Human layout from a reference photo: pose.
   - ADE20K-like scene layout: segmentation.
   - Coarse geometry and relative distance: depth.
   - Fine geometry and surface orientation: normal map.
2. Check whether the user wants metadata inspection or real image generation. For inspection, use the bundled AST helper; for generation, prepare the original app environment and model files before launching any Gradio script.
3. Route detector-only threshold interpretation and preprocessing behavior to `../annotators-and-preprocessing/SKILL.md`; keep this sub-skill focused on app wiring and inference controls.

## Prepare Model Files For Real App Runs

The app launch scripts expect these relative files from the ControlNet checkout root:

- Shared config: `models/cldm_v15.yaml`.
- ControlNet weights: `models/control_sd15_canny.pth`, `models/control_sd15_mlsd.pth`, `models/control_sd15_hed.pth`, `models/control_sd15_scribble.pth`, `models/control_sd15_openpose.pth`, `models/control_sd15_seg.pth`, `models/control_sd15_depth.pth`, or `models/control_sd15_normal.pth` depending on app.
- Detector weights under `annotator/ckpts` for HED, MiDaS, OpenPose, Uniformer, and related annotators when those apps are used.
- A Python environment compatible with the repository's `environment.yaml`; install the documented Gradio dependency before launching apps, because Gradio may be absent in minimal inspection environments.

Do not download model files automatically from skill scripts. If the user asks to run an app, tell them which files are required and ask for permission before any network download.

## Launch Or Adapt An App Safely

1. Before launch, confirm the user actually wants a Gradio server. The original scripts call `block.launch(server_name='0.0.0.0')`, exposing the app on all interfaces unless edited or firewalled.
2. Run from the ControlNet checkout root so relative `models/...` and `annotator/ckpts/...` paths resolve.
3. For local-only testing, adapt the launch call to a safer bind address such as localhost if the user's Gradio version supports it.
4. Do not import launch scripts from another Python module for introspection. Use the AST helper for metadata or copy/adapt the `process(...)` logic into a controlled script where model loading and server launch happen only under an explicit main guard.
5. When adapting a `process(...)` function, preserve the parameter order expected by the Gradio `ips` list and keep detector-specific controls after the shared controls.

## Configure Prompts And Guidance

- `prompt` is combined with `a_prompt` as `prompt + ', ' + a_prompt`; the default added prompt is `best quality, extremely detailed`.
- `n_prompt` defaults to a long negative quality/anatomy prompt and is used for unconditional guidance text.
- `scale` controls unconditional guidance strength; the default is 9.0 for normal prompted generation.
- `ddim_steps` defaults to 20; increase steps for difficult controls or guess mode at the cost of runtime.
- `eta` defaults to 0.0 for deterministic DDIM-style sampling, but deterministic output still depends on seed and CUDA/runtime behavior.

## Use Guess Mode

Guess mode changes two parts of the pipeline:

- Unconditional conditioning omits the control tensor: `un_cond['c_concat'] = None`.
- `model.control_scales` becomes a decaying 13-element schedule: `strength * (0.825 ** (12 - i))` for layer index `i`; without guess mode, all 13 scales equal `strength`.

The README describes guess mode as non-prompt mode where the ControlNet encoder tries to infer content from the control map. For promptless guess-mode experiments, start around 50 DDIM steps and guidance scale 3-5, then adjust `strength` and detector thresholds. Users may still provide prompts in guess mode; the mode does not require empty prompts.

## Choose Resolution, Strength, And Seed

- Lower `image_resolution` reduces VRAM and speeds generation; the app range is 256-768 with default 512.
- Lower `detect_resolution` reduces detector cost and control detail for apps that expose it; depth/normal default to 384 while most other detector apps default to 512.
- Increase `strength` when the generated image ignores the control map; decrease it when control artifacts dominate or guess-mode outputs are too literal.
- Set a fixed non-negative `seed` when comparing apps or parameters. Leave `seed=-1` only when nondeterministic random exploration is desired.
- Reduce `num_samples` first when debugging memory, then reduce `image_resolution`, then reduce detector resolution for apps that expose it.

## Prepare Low VRAM Settings

`config.save_memory` is `False` by default. Setting it to `True` makes the Gradio `process(...)` functions call `model.low_vram_shift(...)` before/after conditioning and diffusion. The repository's low-VRAM note recommends this mode for 8GB GPUs or larger batch sizes, but warns that it was still being tested and not guaranteed on all graphics cards.

When advising a low-VRAM run:

1. Enable the save-memory flag in the working checkout's `config.py` only when the user is maintaining or running that checkout.
2. Keep `num_samples=1` for the first smoke run.
3. Start at `image_resolution=512` or lower; reduce to 384/448 if OOM persists.
4. Use lower `detect_resolution` for HED, fake scribble, pose, segmentation, depth, normal, or M-LSD if detector memory is the problem.
5. Avoid promising success: low-VRAM mode can help but cannot overcome missing CUDA, incompatible dependencies, insufficient memory for checkpoints, or oversized batches.

## Extract Signatures In CI

For CI or documentation checks without GPU, checkpoints, Gradio, or detectors, run the bundled helper instead of importing source scripts:

```bash
python sub-skills/gradio-inference-apps/scripts/extract_gradio_signatures.py --repo-root /path/to/ControlNet
```

The helper parses `gradio_*2image.py` files with Python `ast`, reports `process(...)` and helper signatures, extracts string references to `models/...` files, and flags top-level `launch`, `create_model`, `load_state_dict`, and detector/sampler construction calls. It does not import app modules or touch checkpoints.
