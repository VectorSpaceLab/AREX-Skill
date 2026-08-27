# Zero123Plus model and camera notes

This reference summarizes the model family, fixed camera layout, and licensing
facts that matter when choosing a generation workflow.

## Model catalog

| Model id | Role | Typical use |
| --- | --- | --- |
| `sudo-ai/zero123plus-v1.1` | Base Zero123Plus model release | Standard single-image to six-view generation and the v1.1 depth ControlNet flow. |
| `sudo-ai/controlnet-zp11-depth-v1` | Depth ControlNet checkpoint | Depth-guided generation on top of the v1.1 base model. |
| `sudo-ai/zero123plus-v1.2` | Base Zero123Plus model release | The v1.2 normal-generation flow and other workflows that want the newer intrinsics handling. |
| `sudo-ai/controlnet-zp12-normal-gen-v1` | Normal-generation ControlNet checkpoint | The v1.2 normal-generator pass that produces the view-space normal grid. |
| `sudo-ai/zero123plus-pipeline` | Custom Diffusers pipeline code | Remote custom-pipeline id; the bundled wrappers default to the checked-in `diffusers-support/` copy instead. |

## Which model should I use?

- Use **v1.1** if you are reproducing the original base or depth workflow.
- Use **v1.2** if you want the newer intrinsics handling, the fixed `30°`
  output field of view, and the normal-generator ControlNet.
- Use the matching ControlNet for the chosen base model family; do not mix the
  v1.1 and v1.2 checkpoints.

## Fixed camera layout

Zero123Plus does not expose free camera control in these workflows. The output
is always a fixed six-view set.

- Relative azimuths: `30, 90, 150, 210, 270, 330` degrees.
- v1.1 elevations: `30, -20, 30, -20, 30, -20` degrees.
- v1.2 elevations: `20, -10, 20, -10, 20, -10` degrees.
- v1.2 field of view: `30°`.

The saved output is a single montage, conventionally treated as a `2 x 3` grid
of six tiles in row-major order:

1. top-left
2. top-right
3. middle-left
4. middle-right
5. bottom-left
6. bottom-right

Keep that ordering if you split it later.

## v1.2 behavior change

The v1.2 release changed the way the model handles intrinsics and cropping:

- it is more robust to a wider range of input FOVs and crops,
- it unifies the output FOV to `30°`, and
- it assumes a normalized object size instead of resizing the object based on
  the input framing.

That means you should still provide a clean, square, well-centered input, but
v1.2 is less brittle when the crop is not perfect.

## License distinction

- **Code**: Apache 2.0.
- **Model weights**: CC-BY-NC 4.0.

Practical takeaway: the outputs can be used freely, but the weights themselves
are non-commercial. If you are adapting the model into a service or product,
check the model-weight license before proceeding.
