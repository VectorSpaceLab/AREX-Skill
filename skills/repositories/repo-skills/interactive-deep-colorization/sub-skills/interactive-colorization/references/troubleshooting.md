# Interactive colorization troubleshooting

Use this reference when a local-hints task fails or the source behavior is surprising.

## Routing checks

| Symptom or question | Action |
| --- | --- |
| Missing PyTorch/Caffe weights, Caffe prototxt/model confusion, PyQt install, display server, Docker image, or dependency setup | Route to [../../setup-and-models/SKILL.md](../../setup-and-models/SKILL.md). |
| Global histogram transfer, reference-image matching, or 313-bin global histogram conditioning | Route to [../../global-histogram-transfer/SKILL.md](../../global-histogram-transfer/SKILL.md). |
| Training the local-hints network | Out of scope for this repository; the repository points training to an external PyTorch colorization project. |
| Need source/API smoke without GUI/Caffe/model weights | Run [../scripts/smoke_core_helpers.py](../scripts/smoke_core_helpers.py) with a checkout supplied via `--repo-root`. |
| Need CLI defaults without GUI imports | Run [../scripts/inspect_cli_defaults.py](../scripts/inspect_cli_defaults.py). |

## CLI parser quirk: `--dist_model` is not independent

Both GUI parser variants define `--dist_model` with `dest='color_model'`:

- There is no `args.dist_model` attribute.
- `--color_model` and `--dist_model` write to the same `args.color_model` field.
- In the PyTorch backend, both the color model and distribution model call `prep_net(... path=args.color_model ...)`.
- If both flags are supplied, the final value is whichever of `--color_model` or `--dist_model` argparse processes last on the command line.

Do not write automation that expects separate PyTorch color and distribution model paths from the shipped parser.

Other parser details:

- The root GUI parser defaults `--backend` to `caffe`; the Docker GUI parser defaults `--backend` to `pytorch`.
- `--cpu_mode` is parsed as a boolean, then the main routine sets `gpu=-1` after initially printing parsed arguments.
- `--win_size` is truncated to a multiple of 4 after parsing.
- `--load_size` is labeled deprecated in source comments but still controls wrapper `Xd`.
- Importing the root GUI script just to inspect parser defaults can fail in minimal/headless environments because GUI dependencies are imported at module top level. Use the bundled static CLI inspection script instead.

## Backend and model issues

| Symptom | Likely cause | Remedy |
| --- | --- | --- |
| Caffe import failure | PyCaffe is not installed or not on the Python import path. | Use setup/model guidance before choosing the Caffe backend. For source-only inspection, avoid Caffe `prep_net`. |
| Caffe model load failure | Prototxt or `.caffemodel` file missing, incompatible, or not downloaded. | Verify model files through setup/model guidance; do not treat source imports as proof of Caffe inference readiness. |
| PyTorch state-dict load failure | Missing converted weights, incompatible state dict, or old InstanceNorm checkpoint buffers. | `ColorizeImageTorch.prep_net` patches old InstanceNorm tracking keys, but it still requires a compatible state dict. Verify the exact model file through setup/model guidance. |
| PyTorch CUDA mismatch | Passing a non-`None` `gpu_id` calls `.cuda()` without selecting a device in the wrapper. | Use CPU (`gpu_id=None`) for minimal checks; for GPU work, ensure the process selects the intended CUDA device externally or through setup policy. |
| Output shape mismatch in PyTorch | Input spatial size not compatible with downsample/upsample skip additions. | Use `Xd=256` or another size divisible by the architecture's downsample schedule. |
| Random colors or poor colorization in smoke checks | Tiny PyTorch architecture checks use random weights and are not quality evaluations. | Use smoke checks only for API/shape validation; use prepared model weights for actual colorization. |

Caffe, PyQt GUI launch, and downloaded model-weight native execution were not verified during construction. Keep those as setup-gated capabilities rather than asserting they work in every environment.

## Image and tensor issues

| Symptom | Likely cause | Remedy |
| --- | --- | --- |
| Image loading crashes near `.copy()` | OpenCV returned `None` for an unreadable image path. | Validate image existence and readability before calling wrapper or GUI image loading. |
| `I need to have an image!` | `net_forward` was called before `load_image` or `set_image`. | Prepare image state first. |
| `I need to have a net!` | `net_forward` was called before successful `prep_net` or before assigning a valid test network in a smoke context. | Prepare a backend model for real inference, or use `SIGGRAPHGenerator` directly for shape-only smoke. |
| Full-resolution helpers fail | `output_ab` or `input_ab` is not set, usually because no successful forward or hint setup occurred. | Call `net_forward` before `get_img_fullres`; set hints before `get_input_img_fullres`. |
| Hint has no effect | Mask is all zeros or has wrong shape/order. | Provide `input_mask` as `1 x Xd x Xd` and `input_ab` as `2 x Xd x Xd`; use binary 0/1 mask values before wrapper normalization. |
| Edge patch behaves unexpectedly | Python slices may be empty or clipped implicitly if indices go out of range. | Clip patch bounds to `[0, Xd)` when adapting the notebook `put_point` helper. |
| API and GUI coordinates are swapped | GUI events are `(x, y)` but array operations are `[h, w]` or `[y, x]`. | Convert explicitly and label coordinates in code. |
| `set_image` gives inconsistent helper shapes | `set_image` does not resize to `Xd`. | Pass an already resized `Xd x Xd x 3` RGB array or use `load_image`. |

## Gamut and suggestion issues

| Symptom | Likely cause | Remedy |
| --- | --- | --- |
| Chosen RGB color changes after selection | The GUI snaps the requested color to the selected pixel's L value and RGB gamut. | Use `lab_gamut.snap_ab` behavior when explaining or reproducing GUI color choices. |
| Suggested colors unavailable | No distribution model was provided, no image is loaded, or distribution `net_forward` has not run. | Prepare the distribution wrapper, set the image, forward current hints, then call `get_ab_reccs`. |
| `get_ab_reccs` prints `Need to set prediction first` | `dist_ab_set` is false. | Call the distribution model's `net_forward` before requesting recommendations. |
| Recommendation confidence misunderstood | Confidence is K-means sample occupancy from a per-pixel color distribution. | Treat it as a ranking hint, not as a calibrated probability that the final image is correct. |
| Gamut click rejected | The current L-specific ab point is outside displayable RGB gamut. | Choose a valid point on the masked gamut map or snap through `snap_ab`. |

## GUI behavior surprises

| Symptom | Explanation |
| --- | --- |
| Freehand strokes do not work | `UIControl.addStroke` is a placeholder in the inspected source. The implemented interaction is point/patch editing. |
| Result recomputes often while dragging | Moving a selected point updates model input and recomputes the result during mouse movement. |
| Palette selection fails before point selection | `set_color` expects an active point position so the color can be snapped at the selected pixel's L value. Select a point first. |
| Recent colors are fewer than edits | Recent colors are de-duplicated before display. |
| Saved output directory name is not deterministic | It includes a timestamp and the method label. Inspect contents rather than relying on exact directory names. |

## Saved artifact interpretation

Prefer `.npy` files for exact data:

- `im_l.npy`: working L channel.
- `im_ab.npy`: user ab hints.
- `im_mask.npy`: user hint mask.

Use PNG files for visualization only. OpenCV writes and reads in BGR order, while most plotting code expects RGB, so convert when comparing displays.
