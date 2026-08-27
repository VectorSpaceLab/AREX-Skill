# iGAN Interactive UI Troubleshooting

Use this reference for launch, display, dependency, model, and interaction
failures in the PyQt4 iGAN GUI. Keep command generation separate from real GUI
execution: the bundled helper can validate command shape without importing the
legacy runtime stack.

## Fast triage order

1. Did the failure happen while running the helper or while launching
   `iGAN_main.py`?
2. If launching the GUI, did Python fail before a window appeared?
3. If a window appeared, did the model load and candidate grid update?
4. Is a display/VNC session available?
5. Does the requested model file exist?
6. Is the active Python environment compatible with PyQt4 and Theano?
7. Is CUDA/cuDNN configured for the selected `THEANO_FLAGS` device?

Do not diagnose CUDA first when the error is a Qt display error; do not diagnose
Qt first when the error is a missing model file.

## Helper command checks

Run:

```bash
python sub-skills/interactive-ui/scripts/build_igan_command.py \
  --model-name outdoor_64 --check-display --check-model-file
```

Expected helper behavior:

- Prints a shell command.
- Emits warnings instead of importing PyQt4 or Theano.
- Exits nonzero only when a strict flag such as `--require-display` or
  `--require-model-file` is used and the corresponding check fails.

If the helper itself fails, it is a generated-skill issue or a Python3 runtime
issue for the helper, not an iGAN GUI runtime issue.

## Symptom: `ImportError: No module named PyQt4`

Likely cause:

- PyQt4 is missing from the active environment.
- The user is running a modern Python environment where PyQt4 wheels/packages are
  unavailable.
- The wrong interpreter was used for the legacy checkout.

Recovery:

1. Confirm the interpreter:
   ```bash
   python -V
   python -c "from PyQt4.QtGui import QApplication; print('pyqt4 ok')"
   ```
2. Use an environment known to provide PyQt4 for the relevant Python version.
3. On old Debian/Ubuntu-style systems, the package names were typically
   `python-qt4` or `python3-pyqt4`; modern distributions may no longer ship
   them.
4. If PyQt4 cannot be installed, do not claim UI runtime support. Use the
   command builder for static planning or route non-UI generation to
   [../../constraint-generation/SKILL.md](../../constraint-generation/SKILL.md).

## Symptom: Qt says no display or no platform plugin

Example signals:

- `QXcbConnection: Could not connect to display`
- `Could not connect to any X display`
- `DISPLAY` is empty
- The process hangs in a headless SSH shell before a window appears

Likely cause:

- The GUI was launched without an X11/desktop session.
- SSH X forwarding is missing or not trusted.
- A remote GPU server is being used without VNC, Xpra, or another desktop path.

Recovery:

1. Check:
   ```bash
   echo "$DISPLAY"
   ```
2. If empty, start or attach to VNC/Xpra/remote desktop before launching.
3. If using SSH X forwarding, reconnect with the appropriate forwarding option
   and verify a small X application works before launching iGAN.
4. If the user only has headless access, do not keep retrying the GUI; route to
   the non-UI constraint workflow.
5. Expect possible display artifacts or latency on remote desktops; this is a
   documented limitation for interactive use on GPU servers.

## Symptom: `ImportError: No module named qdarkstyle`

Likely cause:

- qdarkstyle is missing. The GUI imports it before constructing the application.

Recovery:

1. Install qdarkstyle into the legacy runtime environment if allowed.
2. If installation is not possible, a local runtime patch can comment out the
   stylesheet import and `load_stylesheet` call, but this changes the checkout
   and should be a conscious workaround.
3. This issue does not imply that Theano, CUDA, or model files are broken.

## Symptom: `ImportError: No module named cv2`

Likely cause:

- OpenCV Python bindings are missing.
- The installed OpenCV version exposes APIs incompatible with this legacy code.

Recovery:

1. Check:
   ```bash
   python -c "import cv2; print(cv2.__version__)"
   ```
2. Install an OpenCV binding compatible with the chosen Python runtime.
3. If ShadowDraw fails later with `cv2.cv.CV_DIST_L2`, the OpenCV binding may be
   too modern for the old `cv2.cv` constant path. Use an older OpenCV package or
   patch the constant to the modern equivalent only after documenting the change.

## Symptom: Python syntax or runtime errors on modern Python

Example signals:

- `SyntaxWarning` or behavior issues from `is` comparisons against strings.
- Old Theano import failures on recent Python versions.
- `np.bool` or other deprecated NumPy alias errors in constraint handling.
- PyQt4 packages unavailable for the selected Python.

Likely cause:

- The project targets a Python2-era scientific stack, while the user is running a
  modern Python/NumPy/Theano combination.

Recovery:

1. Prefer a pinned legacy environment over ad hoc patches.
2. Keep NumPy, Theano, OpenCV, and PyQt4 versions mutually compatible.
3. Treat helper success as static command success only; it does not validate the
   old GUI runtime.
4. If the user asks for a port, record this as a modernization task outside this
   sub-skill's runtime operation boundary.

## Symptom: `AttributeError: 'NoneType' object has no attribute 'Model'`

Likely cause:

- Dynamic lookup of `model_def.<model_type>` failed.
- `--model_type` was misspelled or no matching module exists.

Recovery:

1. Use the default unless the checkout was extended:
   ```bash
   --model_type dcgan_theano
   ```
2. Keep `--framework theano` paired with `--model_type dcgan_theano`.
3. If using a custom backend, verify both a model module and a matching
   constrained optimizer module exist in the checkout.

## Symptom: `AttributeError: 'NoneType' object has no attribute 'OPT_Solver'`

Likely cause:

- Dynamic lookup of `constrained_opt_<framework>` failed.
- `--framework` was changed without adding a corresponding optimizer module.

Recovery:

1. Use:
   ```bash
   --framework theano
   ```
2. If a custom framework is required, implement and import-test the matching
   optimizer outside the UI session before launching.
3. Do not treat model-file presence as proof that the optimizer module exists.

## Symptom: model file not found

Likely cause:

- The default file `models/<model_name>.<model_type>` is absent.
- The user downloaded a differently named file or placed it outside `models/`.
- `--model_name` and `--model_type` do not match the artifact suffix.

Recovery:

1. Ask the model-inference sub-skill for artifact URL/download guidance.
2. Verify the expected path:
   ```bash
   ls models/outdoor_64.dcgan_theano
   ```
3. Or pass an explicit file:
   ```bash
   python iGAN_main.py --model_name outdoor_64 --model_file path/to/file.dcgan_theano
   ```
4. For ShadowDraw, use `hed_shoes_64` and the matching `hed_shoes_64.dcgan_theano`
   artifact when possible.

## Symptom: Theano cannot use GPU or cuDNN

Example signals:

- Theano reports CPU device despite `device=gpu0`.
- CUDA compiler or `nvcc` not found.
- cuDNN version mismatch errors.
- The process starts but per-edit updates are extremely slow.

Likely cause:

- CUDA/cuDNN stack is missing or too new/old for the installed Theano.
- `THEANO_FLAGS` selects the wrong GPU.
- Driver/runtime mismatch.

Recovery:

1. Confirm the intended flags:
   ```bash
   echo "$THEANO_FLAGS"
   ```
2. Build a command with explicit device:
   ```bash
   python sub-skills/interactive-ui/scripts/build_igan_command.py \
     --model-name outdoor_64 --device gpu0
   ```
3. Run the model-inference smoke workflow if available before launching the GUI;
   it isolates model/Theano issues from Qt interaction.
4. If only CPU is available, warn that UI operation may not be real-time and that
   full native UI verification remains blocked.

## Symptom: window opens but candidate grid stays blank

Likely cause:

- The model did not load or did not generate initial images.
- The optimizer thread is running but cannot complete Theano generation.
- No constraints have been applied yet, or `--n_iters` has not completed.
- `--top_k`/`--batch_size` combination is too large for available memory.

Recovery:

1. Watch stdout for model or Theano errors behind the Qt window.
2. Draw one short stroke and wait for optimizer progress text.
3. Reduce workload:
   ```bash
   --batch_size 16 --top_k 4 --n_iters 10
   ```
4. Verify the model with a non-UI sample-generation smoke case through the
   model-inference sub-skill.
5. If the GUI remains responsive but images never appear, treat it as a model or
   optimizer runtime failure rather than a brush-control problem.

## Symptom: edits appear but generated result ignores them

Likely cause:

- Too few optimization iterations.
- The selected model cannot represent the requested content.
- The user is drawing constraints too dense or contradictory.
- The candidate displayed is not the candidate that best satisfies constraints.

Recovery:

1. Increase `--n_iters` modestly, for example from 40 to 60.
2. Use shorter strokes and wait for updates.
3. Click alternate candidate thumbnails.
4. Use Fix before adding detailed edits.
5. Explain that iGAN only searches the model's learned natural image manifold;
   arbitrary drawings may not be satisfiable.

## Symptom: ShadowDraw command produces poor guidance

Likely cause:

- The model is not `hed_shoes_64` or does not represent sketch-trained shoes.
- `--shadow` was used without `--average`.
- OpenCV distance-transform compatibility issues affect the cue.

Recovery:

1. Prefer:
   ```bash
   python iGAN_main.py --model_name hed_shoes_64 --shadow --average
   ```
2. Confirm the `hed_shoes_64.dcgan_theano` model file exists.
3. Try toggling black/white with the color chip.
4. If an OpenCV constant error appears, address OpenCV compatibility first.

## Symptom: Warping does nothing

Likely cause:

- The source patch was not selected with right-click first.
- No generated image was available when right-click happened.
- ShadowDraw mode disables Warping by design.
- Patch size is too small or too large for the current pad scale.

Recovery:

1. In normal mode, draw color/sketch constraints and wait for an image.
2. Select Warping.
3. Right-click the source region.
4. Left-drag to the target position.
5. Use the mouse wheel to change patch size.
6. Do not use `--shadow` when warping is required.

## Symptom: slider or Play has no visible effect

Likely cause:

- No morph sequence has been generated yet.
- The current edit has not reached `--n_iters`.
- There are no candidate images available.

Recovery:

1. Draw a short stroke and wait for optimization to finish.
2. Watch for morph-generation text in stdout.
3. Try a smaller `--n_iters` for a quick smoke session.
4. Use the slider only after candidates appear.

## Symptom: Save dialog or output confusion

Likely cause:

- First Save opens a folder picker; this is expected.
- The default folder is relative to the runtime checkout and model name.
- The user cancelled the dialog or selected a folder without write permission.

Recovery:

1. Press Save again after selecting a writable folder.
2. Check stdout for `save the result to (...)`.
3. Look for an HTML/image output in the selected folder.
4. If running over remote desktop, ensure the dialog is not hidden behind the
   main window.

## Symptom: remote UI latency or artifacts

Likely cause:

- VNC or remote desktop adds latency.
- GPU server display forwarding is not optimized for rapid Qt repainting.
- Candidate generation competes with display rendering.

Recovery:

1. Lower `--batch_size`, `--top_k`, and `--n_iters` for interactive debugging.
2. Use a lower `--win_size`.
3. Prefer a remote desktop that runs near the GPU host rather than forwarding
   every Qt paint event over a slow link.
4. If the task does not need manual drawing, route to headless constraints.

## Minimal report template

When reporting a blocked UI launch, include:

- Command attempted or helper-generated command.
- Whether `DISPLAY` was set.
- Python version and whether PyQt4/qdarkstyle/cv2 imports succeeded.
- Requested model name and whether the model file existed.
- `THEANO_FLAGS` device string.
- Last stdout/stderr line before failure.
- Whether the window appeared and whether candidates updated.
- Recovery path chosen: display setup, dependency fix, model-inference smoke,
  headless constraint route, or modernization task.
