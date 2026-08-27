# Input Formats and Assets

## Reference Image Contract

Make-It-3D is designed around a single reference image with a foreground alpha mask.

Source-derived behavior:

- `main.py` reads `--ref_path` with `cv2.IMREAD_UNCHANGED`.
- It immediately calls `cv2.cvtColor(ref_imgs, cv2.COLOR_BGRA2RGBA)`, so a four-channel BGRA-style image is expected.
- It resizes the image to `512 x 512`.
- It composites RGB over white using alpha.
- It erodes the alpha mask with a `5 x 5` kernel and treats zero alpha as background for the depth mask.

Practical requirements:

```text
format: PNG recommended
channels: RGBA/BGRA with alpha
object: centered, single foreground object
background: transparent outside the object
resolution: any reasonable input; source resizes to 512 x 512
mask: avoid holes, noisy edges, and large background islands
```

Run the bundled validator before training:

```bash
python /path/to/skill/sub-skills/environment-and-inputs/scripts/validate_alpha_input.py --image ref_alpha.png
```

## Prompt and Captioning

If `--text` is omitted, `main.py` loads BLIP2 and generates a caption. The code then removes phrases such as `there is`, changes `close up` to `photo`, and replaces black/white background wording with `ground`.

For reproducibility and lower resource use, prefer:

```bash
--text "a detailed description of the foreground object"
```

Use `--negative` to pass a negative prompt. Use `--need_back` when back-view text conditioning is needed for 360-degree completion.

## DPT Weights

The main pipeline hard-codes:

```text
dpt_weights/dpt_hybrid-midas-501f0c75.pt
```

The DPT CLI utilities have their own `weights/` defaults, but `main.py` expects `dpt_weights/`. If the user stores weights elsewhere, either create the expected layout or deliberately patch the source.

## Hugging Face Assets

Default Stable Diffusion model mapping in `nerf/sd.py`:

| Flag | Model id |
| --- | --- |
| `--sd_version 2.0` | `stabilityai/stable-diffusion-2-base` |
| `--sd_version 1.5` | `runwayml/stable-diffusion-v1-5` |
| `--hf_key MODEL` | custom Hugging Face model id |

Ask before downloads if model assets are not cached. Do not place tokens in commands shown back to the user.
