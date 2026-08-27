---
name: interactive-ui
description: "Launch and operate the legacy PyQt4 iGAN interactive interface,
  drawing tools, candidate grid, slider, control panel, AverageExplorer, and
  ShadowDraw modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# interactive-ui

Use this sub-skill when the task is to open, configure, explain, or troubleshoot
`iGAN_main.py`, the PyQt4 interactive drawing interface for iGAN.

## Read First

1. For launch recipes and preflight commands, read
   [references/ui-workflows.md](references/ui-workflows.md).
2. For what each visible widget, brush, slider, shortcut, and mode does, read
   [references/controls-reference.md](references/controls-reference.md).
3. For concrete failure diagnosis, read
   [references/troubleshooting.md](references/troubleshooting.md).
4. For pretrained model files, sample generation smoke tests, and artifact URLs,
   route to [../model-inference/SKILL.md](../model-inference/SKILL.md).
5. For headless color/mask/edge-map constraint generation, route to
   [../constraint-generation/SKILL.md](../constraint-generation/SKILL.md).

## Use When

- The user wants a dry command for launching the iGAN GUI.
- The task mentions PyQt4, drawing pad, candidate results, color/sketch/warp
  brushes, slider interpolation, Play/Fix/Restart/Save/Edits, AverageExplorer,
  or ShadowDraw.
- The user asks how to operate the interactive interface once it appears.
- The user asks why the UI fails to open, opens blank, cannot import PyQt4,
  cannot find a display, cannot load a model, or does not update candidates.
- The user needs an optional native verification candidate for an interactive
  launch but has not asked to run a GPU/UI session yet.

## Do Not Use When

- The user only wants non-UI generation from color masks and edge maps; use
  [../constraint-generation/SKILL.md](../constraint-generation/SKILL.md).
- The user asks to download DCGAN/AlexNet artifacts or generate sample grids;
  use [../model-inference/SKILL.md](../model-inference/SKILL.md).
- The user asks to train DCGAN models, create HDF5 datasets, or pack training
  checkpoints; use [../training-data/SKILL.md](../training-data/SKILL.md).
- The user asks to project an image into latent space; use the projection
  sub-skill if present, not this UI router.
- The user asks to modernize or port the code to a new framework; this sub-skill
  can identify UI dependencies, but it does not own a rewrite plan.

## Runtime Facts To Preserve

- `iGAN_main.py` is a legacy script that imports PyQt4, qdarkstyle, Theano model
  definitions, and a framework-specific constrained optimizer during startup.
- The documented runtime assumes Python2-era packages, Theano, OpenCV, CUDA,
  cuDNN, and a desktop display or VNC session.
- The default model command uses `--model_name outdoor_64` and resolves the model
  file to `./models/<model_name>.<model_type>` when `--model_file` is omitted.
- `--model_type` defaults to `dcgan_theano`; `--framework` defaults to `theano`
  and selects `constrained_opt_theano` through dynamic lookup.
- `--top_k` controls the maximum number of candidate thumbnails; `--batch_size`
  controls random initial latent samples used by optimization.
- `--n_iters` controls per-edit constrained optimization iterations; real-time
  behavior depends on a compatible GPU stack.
- `--morph_steps` controls slider/playback frames between the previous result
  and the current edited result.
- `--average` enables AverageExplorer display, where the main pad may show a
  weighted average of candidate results.
- `--shadow` enables ShadowDraw-style sketch assistance and disables color and
  warp buttons in favor of sketching.
- `hed_shoes_64` is the documented model for ShadowDraw and should normally be
  combined with `--shadow --average`.

## Build Launch Commands Safely

Use the bundled dry-run helper instead of importing or executing the GUI:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py --help
python sub-skills/interactive-ui/scripts/build_igan_command.py \
  --model-name outdoor_64 --check-display
```

For ShadowDraw with AverageExplorer:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py \
  --model-name hed_shoes_64 --shadow --average --check-display
```

The helper prints the `THEANO_FLAGS` environment and `python iGAN_main.py ...`
command but never launches PyQt4, never loads a model, never downloads files,
and never touches CUDA.

## Launch Readiness Checklist

Before telling the user to run the command, confirm these facts from
[references/ui-workflows.md](references/ui-workflows.md):

- A compatible Python/PyQt4/OpenCV/qdarkstyle stack is active.
- The requested pretrained model file exists under the expected `models/` path
  or the user supplied `--model_file`.
- The display is available through local X11, VNC, Xpra, or another remote
  desktop path; a bare SSH shell without `DISPLAY` is not enough.
- `THEANO_FLAGS` selects the intended device, usually `device=gpu0,floatX=float32`
  for the legacy real-time path.
- The user understands that modern Python and modern CUDA may need pinning,
  compatibility shims, or a container built for the old Theano stack.

## Operate The UI

- Explain the window as a drawing pad on the left and a candidate grid on the
  right; details live in [references/controls-reference.md](references/controls-reference.md).
- For color edits, choose Coloring, right-click the color chip or pad to select
  a color, drag with left mouse, and use the wheel to change brush width.
- For shape edits, choose Sketching and drag with left mouse; in ShadowDraw mode
  this is the primary enabled tool and color toggles between black and white.
- For warping, first create color/sketch constraints, right-click a square
  source patch, then left-drag the patch target; use the wheel for patch size.
- Candidate thumbnails update during constrained optimization; click a thumbnail
  to select it for the main drawing pad.
- The slider and Play button inspect morph frames after an edit; Fix promotes the
  current image/frame as the next latent starting point.
- Restart clears the UI state; Save writes an HTML/image result in the user-chosen
  output folder after the first save dialog.
- Keyboard shortcuts include `P`, `F`, `R`, `S`, `E`, `A`, and `Q`.

## Troubleshooting Routing

- If import fails before a window appears, start with dependency and Python
  version rows in [references/troubleshooting.md](references/troubleshooting.md).
- If a Qt error says no platform/display is available, diagnose display/VNC
  setup before touching Theano or model files.
- If the window opens but candidates never update, inspect CUDA/Theano/model
  loading, the `constrained_opt_theano` dynamic import, and optimizer logs.
- If ShadowDraw is requested with a non-sketch model, recommend `hed_shoes_64`
  or explain that other models may not provide useful sketch guidance.
- If the user wants to bypass the UI after display problems, route to
  [../constraint-generation/SKILL.md](../constraint-generation/SKILL.md).

## Native Verification Candidate

Preserve the optional native case as a blocked/unverified runtime launch unless
all prerequisites are available:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_main.py --model_name outdoor_64
```

Expected signal: a PyQt4 window titled `Interactive GAN` opens, model arguments
print to stdout, the candidate grid updates after a stroke, and quitting with
`Q` exits the application. Do not run this case in an automated verification
session without explicit UI, model-file, and GPU approval.
