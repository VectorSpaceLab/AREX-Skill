# iGAN Interactive Controls Reference

Use this reference when a user asks how to operate the PyQt4 interface after it
opens. It explains the visible layout, mouse interactions, keyboard shortcuts,
mode behavior, and save semantics distilled from the UI widgets.

## Window layout

The main window is a fixed-size PyQt4 widget titled `Interactive GAN`.

| Region | Purpose | Source behavior |
| --- | --- | --- |
| Drawing Pad | Main canvas where generated image and user edits are shown | left side, square, size from `--win_size` |
| Slider Bar | Chooses interpolation frame between previous and current result | horizontal under the drawing pad |
| Brush Tools | Radio buttons for Coloring, Sketching, and Warping | under the slider |
| Color Chip | Displays current color or toggles ShadowDraw black/white | small button near brush tools |
| Edits checkbox | Shows or hides recorded UI strokes over the generated image | checked by default |
| Candidate Results | Grid of optimized candidate outputs | right side, green rectangle marks selected image |
| Control Panel | Play, Fix, Restart, Save buttons | below candidate grid |

The candidate grid width is derived from `--top_k`; by default `top_k=16` gives a
4x4 grid. The selected candidate index is shared between the grid and drawing
pad.

## Startup state

Normal mode:

- Coloring is selected by default.
- The color chip starts green.
- Sketching and Warping are available.
- The Drawing Pad displays generated content once the optimizer has produced
  images.

ShadowDraw mode (`--shadow`):

- Sketching is selected by default.
- Coloring and Warping radio buttons are disabled.
- The color chip starts black and toggles black/white.
- Mouse tracking is enabled for shadow guidance.
- Shadow cues are most meaningful with `--average` and a sketch-oriented model.

AverageExplorer mode (`--average`):

- The drawing pad can display a weighted average of the current candidate set.
- Press `A` to toggle average mode during the session.
- Average mode requires candidate weights from the optimizer; before any useful
  candidates exist, it may show no meaningful image.

## Drawing Pad behavior

The Drawing Pad displays, in priority order:

1. The selected generated image or selected interpolation frame.
2. An AverageExplorer image if average mode is active and weights are available.
3. ShadowDraw cursor cue when both shadow and average modes are active.
4. Current in-progress stroke or warp cursor.
5. Recorded edits if Edits is enabled.

The pad scales from generated model image size to `--win_size`. A 64x64 model and
`--win_size 384` produce a scale factor of 6.

## Coloring brush

Use Coloring to apply local color constraints.

| Action | Effect |
| --- | --- |
| Select `Coloring` | Sets edit type to color and restores previous selected color |
| Right-click | Opens the color picker in normal mode |
| Left press + drag | Paints a stroke and repeatedly updates constraints |
| Mouse wheel | Changes brush width, clamped by the color tool |
| Left release | Saves the stroke into the edit recorder and commits constraints |

Implementation behavior:

- The color tool stores an RGB color image and a one-channel mask.
- Stroke coordinates are downscaled from window pixels to model pixels.
- Constraint updates trigger the optimizer while dragging.
- Recorded color strokes are redrawn over the generated image when Edits is on.

Common advice:

- Use short strokes first; each drag restarts optimization.
- If updates are slow, reduce `--batch_size`, `--top_k`, or `--n_iters` before
  trying longer strokes.

## Sketching brush

Use Sketching to outline object shape or add fine detail.

| Action | Effect |
| --- | --- |
| Select `Sketching` | Sets edit type to edge/sketch |
| Left press + drag | Draws an edge stroke and updates edge constraints |
| Right-click | Changes color in normal mode; toggles black/white in ShadowDraw mode |
| Mouse wheel | Changes sketch width |
| Left release | Records the sketch stroke and commits constraints |

Implementation behavior:

- Normal sketch strokes are drawn as gray dotted overlays in the recorder.
- The edge constraint image is white-on-black or black/white depending on mode
  and selected color.
- ShadowDraw mode uses a one-channel constraint path and a wider default sketch
  width.

Common advice:

- In normal mode, combine Coloring first and Sketching second for more stable
  results.
- In ShadowDraw mode, sketch lightly and let average/shadow feedback guide the
  next stroke.

## Warping brush

Use Warping to move a local image patch after color/sketch constraints have
already produced a recognizable candidate.

| Action | Effect |
| --- | --- |
| Select `Warping` | Sets edit type to warp and displays a square cursor |
| Right-click | Captures a square source patch from the current generated image |
| Left press + drag | Moves the active patch target and updates warp constraints |
| Mouse wheel | Changes square patch size |
| Left release | Commits constraints and resets temporary warp state |

Implementation behavior:

- The warp tool stores source points, destination points, patch widths, and patch
  image snapshots.
- The warp constraint is converted into both color and edge constraints for the
  optimizer.
- Patch size is clamped; at high `--win_size`, one wheel notch changes the source
  patch by a larger model-pixel amount.

Common advice:

- Warping is not the best first edit; use Coloring/Sketching to place the object
  before moving a part.
- If right-click happens before any generated image exists, the patch cannot be
  captured usefully.

## Candidate Results grid

The grid shows up to `--top_k` generated candidates after an optimizer update.

| Action | Effect |
| --- | --- |
| Left-click thumbnail | Selects candidate and updates the Drawing Pad |
| Green rectangle | Marks selected candidate when more than one candidate exists |
| Slider move | Changes frame displayed for every candidate |
| Restart | Clears candidate images until the optimizer produces new results |

Candidate selection is modulo the available image count. If the optimizer
returns fewer than `top_k` images, only returned images are displayed.

## Slider and morph sequence

The slider selects an interpolation frame after a completed edit. Its range is
`0` to `morph_steps - 1`.

- Moving the slider calls both the drawing pad and candidate grid frame setters.
- `Play` starts at frame 0 and advances through all available frames.
- `Constrained_OPT` generates the morph sequence only after the edit reaches
  `--n_iters` iterations.
- If no sequence exists yet, the slider has no meaningful generated frame to
  display.

Use the slider to inspect how the latent code moves from the previous fixed
state to the current constrained solution.

## Control panel buttons

| Button | Shortcut | Effect |
| --- | --- | --- |
| Play | `P` | Plays the current morph sequence at about 10 FPS |
| Fix | `F` | Uses the selected image/frame latent vector as the next starting point |
| Restart | `R` | Resets optimizer state, UI recorder, tools, candidates, and slider state |
| Save | `S` | Opens a folder picker on first save, then appends generated images to HTML |
| Edits checkbox | `E` | Toggles display of recorded strokes and UI overlays |
| Average toggle | `A` | Toggles AverageExplorer mode even though the checkbox is commented out |
| Quit | `Q` | Prints elapsed time and closes the window |

`Save` writes under the folder selected in the dialog. The default suggested
folder is `web/<model_name>` relative to the runtime checkout, but the user can
choose another destination.

## Fix semantics

`Fix` calls `init_z(frame_id, image_id)` on the optimizer:

- It extracts the selected latent vector from the current sequence.
- It creates new nearby latent initializations around that vector.
- It increases smoothness relative to the fixed latent state.
- The next edit refines from this fixed result rather than the original random
  initialization.

Use `Fix` after selecting a promising candidate and frame, especially before
adding detailed color, sketch, or warp constraints.

## Edits display semantics

`Edits` toggles `show_ui` in the drawing widget:

- When on, current strokes, recorded strokes, and warp cursors are visible over
  generated content.
- When off, the generated image is easier to inspect without edit overlays.
- Toggling Edits does not remove constraints; it only changes visualization.

If the result appears unchanged after hiding Edits, explain that constraints are
still active until Restart or a new fixed state is chosen.

## Suggested guided session

1. Launch `outdoor_64` or another non-shadow model.
2. Draw one short Coloring stroke.
3. Wait for the candidate grid to update.
4. Click two different thumbnails and observe the main pad.
5. Drag the slider and press Play.
6. Choose a good frame/candidate and press Fix.
7. Add a short Sketching stroke.
8. Toggle Edits to compare raw generated image vs. overlays.
9. Save the result if the user needs an output record.
10. Quit with `Q`.

## Suggested ShadowDraw session

1. Launch `hed_shoes_64` with `--shadow --average`.
2. Confirm Sketching is selected and other brushes are disabled.
3. Draw a short shoe outline stroke.
4. Use the black/white color chip toggle if the sketch sign is not helpful.
5. Watch the shadow/average feedback near the cursor.
6. Click candidates only if the grid shows multiple useful options.
7. Press `A` to compare average vs. selected candidate.
8. Press Fix before refining a promising outline.

## Quick symptom hints

- Brush buttons do not respond in ShadowDraw: expected for Coloring/Warping.
- Slider does nothing: no morph sequence has been generated yet or candidates
  have not updated.
- Save asks for a folder: expected on first save.
- Green rectangle absent: only one candidate may be shown or the grid has not
  updated yet.
- UI is responsive but images are blank: inspect model/optimizer runtime, not
  mouse controls.

For recovery actions, use [troubleshooting.md](troubleshooting.md).
