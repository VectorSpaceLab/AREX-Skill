# iGAN Interactive UI Workflows

This reference is the self-contained operating guide for the PyQt4 iGAN GUI.
Use it to prepare a command, check launch prerequisites, and choose the correct
mode. The bundled helper builds commands only; it does not open the interface.

## What the GUI launch does

`iGAN_main.py` performs these startup steps:

1. Parse command-line flags for model, optimization, display size, and UI mode.
2. Resolve `model_file` to `./models/<model_name>.<model_type>` when omitted.
3. Dynamically locate `model_def.<model_type>.Model`.
4. Dynamically locate `constrained_opt_<framework>.OPT_Solver`.
5. Build a `Constrained_OPT` worker thread around the optimizer.
6. Start a PyQt4 `QApplication` with the `GUIDesign` widget.
7. Apply qdarkstyle, set the iGAN logo, fix the window size, show the window,
   and enter the Qt event loop.

Because imports happen near the top of the script, missing PyQt4 or qdarkstyle
can fail before argparse help is displayed in a legacy environment.

## Build a launch command without side effects

From the generated iGAN skill root, run:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py --help
```

Default outdoor model command:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py \
  --model-name outdoor_64 --check-display
```

ShadowDraw + AverageExplorer command:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py \
  --model-name hed_shoes_64 --shadow --average --check-display
```

JSON output for automation:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py \
  --model-name hed_shoes_64 --shadow --average --format json
```

The helper prints a shell command equivalent to:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_main.py --model_name outdoor_64
```

The helper never imports PyQt4, Theano, OpenCV, or iGAN modules; never opens a
window; never downloads model files; and never probes CUDA beyond optional text
checks that you explicitly request.

## Launch prerequisites

A real UI launch needs all of the following:

| Requirement | Why it matters | Quick signal |
| --- | --- | --- |
| Legacy Python runtime | The repository was written for Python2-era APIs and PyQt4 | imports use PyQt4 and old Theano conventions |
| PyQt4 | Provides `QApplication`, `QWidget`, controls, drawing, and events | `from PyQt4.QtGui import QApplication` succeeds |
| qdarkstyle | Applies the dark Qt stylesheet | `import qdarkstyle` succeeds |
| OpenCV Python bindings | Resizes images, draws lines, computes ShadowDraw distance transforms | `import cv2` succeeds |
| Theano + optimizer module | Loads the DCGAN model and solves constraints | `constrained_opt_theano` imports in the active checkout |
| CUDA/cuDNN-era GPU stack | Needed for interactive speed and many Theano model paths | Theano can select `device=gpu0` |
| Pretrained model file | The GUI creates the model before opening the useful UI | requested `models/<name>.<type>` exists |
| Desktop display | Qt cannot show the window in a headless shell | `DISPLAY` is set or a VNC/Xpra display is active |

A modern Python-only environment can still use the bundled command builder and
static guidance, but that is not proof that the interactive GUI can run.

## Model and framework flags

The UI script accepts these important flags:

| Flag | Default | Runtime effect |
| --- | --- | --- |
| `--model_name` | `outdoor_64` | Selects model identity and default output/save namespace |
| `--model_type` | `dcgan_theano` | Selects `model_def.<model_type>.Model` and default file suffix |
| `--model_file` | derived | Overrides `./models/<model_name>.<model_type>` |
| `--framework` | `theano` | Selects `constrained_opt_<framework>.OPT_Solver` |
| `--win_size` | `384` | Main drawing pad pixel size; coerced to a multiple of 4 |
| `--batch_size` | `64` | Number of latent candidates optimized per edit |
| `--top_k` | `16` | Max thumbnails shown in the candidate grid |
| `--n_iters` | `40` | Per-edit optimization iterations before morph sequence generation |
| `--morph_steps` | `16` | Number of slider/playback frames between previous and current result |
| `--d_weight` | `0.0` | Weight for discriminator realism cost in the optimizer |
| `--interp` | `linear` | Latent interpolation method, typically `linear` or `slerp` |
| `--average` | off | Enables AverageExplorer weighted-average visualization |
| `--shadow` | off | Enables ShadowDraw sketch-assistance mode |

Keep `--model_type dcgan_theano` and `--framework theano` together unless the
checkout has been extended with matching model and optimizer modules. If one is
changed without the other, dynamic lookup can fail or construct incompatible
objects.

## THEANO_FLAGS recipes

Recommended legacy GPU command:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_main.py --model_name outdoor_64
```

Select a different GPU:

```bash
THEANO_FLAGS='device=gpu1,floatX=float32,nvcc.fastmath=True' \
python iGAN_main.py --model_name outdoor_64
```

CPU-only experiments are generally not suitable for interactive operation. If a
user insists on CPU diagnostics, build the command with `--device cpu` and warn
that successful startup does not validate real-time use:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py \
  --model-name outdoor_64 --device cpu
```

## Standard launch flow

1. Activate the environment that contains the legacy GUI stack.
2. Confirm display access:
   ```bash
   echo "$DISPLAY"
   ```
   If empty, start or attach to a desktop session before launching.
3. Confirm the requested model file exists. For default arguments, the expected
   file is `models/outdoor_64.dcgan_theano` relative to the checkout where the
   UI will run.
4. Generate a dry command:
   ```bash
   python sub-skills/interactive-ui/scripts/build_igan_command.py \
     --model-name outdoor_64 --check-display --check-model-file
   ```
5. Review warnings from the helper. Resolve missing display or model artifacts
   before attempting a real launch.
6. Copy the printed shell command into the legacy runtime shell.
7. Wait for the argument dump and the `Interactive GAN` window.
8. Draw one short color or sketch stroke and watch for candidate thumbnails to
   refresh. This is the practical smoke signal for model + optimizer + UI.
9. Quit with `Q` or close the window.

## ShadowDraw + AverageExplorer workflow

ShadowDraw is intended for the `hed_shoes_64` sketch model. Build the command:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py \
  --model-name hed_shoes_64 --shadow --average --check-display --check-model-file
```

Expected real launch command shape:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_main.py --model_name hed_shoes_64 --average --shadow
```

Operational notes:

- ShadowDraw starts in Sketching mode.
- Coloring and Warping controls are disabled by design.
- The color chip toggles between black and white rather than opening the normal
  color picker.
- Mouse tracking is enabled so the shadow cue can follow the cursor.
- With `--average`, the main pad can show a weighted average of candidate images;
  press `A` to toggle average mode during the session.

If the user asks for ShadowDraw with `outdoor_64`, `church_64`, `handbag_64`, or
`shoes_64`, explain that the command can be built but the documented sketch
assistance target is `hed_shoes_64`.

## AverageExplorer-only workflow

AverageExplorer can be used without ShadowDraw:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py \
  --model-name outdoor_64 --average
```

During the UI session:

1. Draw constraints.
2. Let candidates update.
3. Use the candidate grid to select modes.
4. Press `A` to toggle average display.
5. Use `Fix` if the current average or selected candidate should become the
   starting point for another edit.

The displayed average is produced by `Constrained_OPT` from cost-derived weights
when weights are available. If no optimized candidates exist yet, average mode
has nothing useful to display.

## Tuning responsiveness

Use conservative changes and explain trade-offs:

| Goal | Candidate setting | Trade-off |
| --- | --- | --- |
| More candidate diversity | increase `--batch_size` | more GPU memory and slower updates |
| Fewer thumbnails | decrease `--top_k` | less mode coverage in the grid |
| Faster edit completion | decrease `--n_iters` | constraints may be less satisfied |
| Smoother playback | increase `--morph_steps` | more sample generation per completed edit |
| Larger drawing pad | increase `--win_size` | larger Qt window; value is rounded down to multiple of 4 |

For troubleshooting, first reduce `--top_k` and `--batch_size` before changing
model code. Keep `--win_size` divisible by 4 or let the script round it.

## Optional native verification case

Only run this when a compatible display, model file, and GPU runtime are
available and the user approves an interactive session:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_main.py --model_name outdoor_64
```

Pass criteria:

- Argument values print to stdout.
- A fixed-size window titled `Interactive GAN` opens.
- A color or sketch stroke triggers optimizer progress text.
- Candidate thumbnails update and one can be selected.
- `P`, `F`, `R`, `S`, `E`, `A`, and `Q` behave as documented in the controls
  reference.

If any prerequisite is absent, record the launch as blocked rather than treating
command construction as runtime success.

## Routing notes

- Use this reference for UI launch and interaction only.
- Use [../../model-inference/SKILL.md](../../model-inference/SKILL.md) for model
  downloads, model-file URL mapping, and non-interactive sample grids.
- Use [../../constraint-generation/SKILL.md](../../constraint-generation/SKILL.md) for
  scripted color/mask/edge constraints without Qt.
- Use [../../training-data/SKILL.md](../../training-data/SKILL.md) for dataset HDF5
  creation and DCGAN training workflows.
