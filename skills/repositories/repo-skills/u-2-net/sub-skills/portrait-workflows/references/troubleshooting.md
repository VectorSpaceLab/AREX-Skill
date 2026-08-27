# Portrait Workflow Troubleshooting

## Missing portrait weights

Symptoms:

- `--weights is required unless --allow-random-weights-for-smoke is set`
- state-dict loading errors

Actions:

1. Obtain a `u2net_portrait.pth`-compatible checkpoint after user approval for any download.
2. Do not substitute `u2net.pth` or `u2netp.pth`; portrait workflows use full `U2NET(3,1)` portrait-trained weights.
3. Use random smoke only for plumbing, not visual quality.

## OpenCV or cascade failure

Symptoms:

- `Failed to import cv2`
- `cascade XML does not exist`
- `OpenCV could not load cascade XML`

Actions:

- Install OpenCV for own-image mode.
- Use the bundled cascade by default; if passing `--cascade`, verify the XML path and format.
- If only portrait-set mode is needed, OpenCV face detection is not required.

## No face detected

Symptoms:

- JSON warning: `no face detected; used whole-image fallback`
- portrait looks weak or off-center

Actions:

- Crop the head manually and rerun in `--mode portrait-set`.
- Try a clearer front-facing image with a large head region.
- Supply a different cascade only if OpenCV's default frontal-face detector is unsuitable.

## Poor portrait quality

Likely causes:

- Head region is much smaller than 512x512.
- Background is cluttered.
- Face is profile, occluded, blurred, or in a group scene.
- Random smoke mode was used.

Actions: verify the checkpoint, input quality, and mode. The README explicitly warns that own-image quality depends on a large, clear head region and relatively clear background.

## Invalid composite controls

Symptoms:

- `--sigma must be a finite number >= 0`
- `--alpha must be a finite number in [0, 1]`

Actions:

- Use nonnegative `--sigma`; README-style composite example uses `20`.
- Use `--alpha` between `0` and `1`; `0.5` gives equal weight to blurred original and portrait map.

## CUDA/device failures

Use `--device cpu` or `--device auto` unless the user specifically requires CUDA. Portrait full U2NET can be slower on CPU but remains functionally valid. If `--device cuda` fails, verify the PyTorch build and driver before retrying.

## Output naming

Portrait maps are `<input-stem>.png`. Composites include sigma/alpha in the filename; decimal points are sanitized to `p` by the bundled script. Use a fresh output directory when comparing parameter sweeps.
