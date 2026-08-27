# Quickstart

## Choose a mode

| Mode | Best for | Default LoRA | Extra requirement |
| --- | --- | --- | --- |
| `normal` | Standard single-image editing | `RiverZ/normal-lora` | Installed packages, CUDA/NVIDIA, and Hub access or cached/local weights |
| `moe` | MoE LoRA inference | `sanaka87/ICEdit-MoE-LoRA` | An ICEdit checkout root containing `icedit/`, passed with `--repo-root` or `ICEDIT_REPO_ROOT` |

`--mode normal` behaves like the normal CLI editing flow.
`--mode moe` behaves like the MoE CLI editing flow.
The bundled helper merges both into one command surface.

## Minimal edit

```bash
python /path/to/ic-edit-skill/sub-skills/inference/scripts/run_icedit_inference.py \
  --mode normal \
  --image /path/to/ic-edit-skill/sub-skills/inference/references/assets/girl.png \
  --instruction "Make her hair dark green and her clothes checked." \
  --seed 304897401
```

## Width handling

- The helper reads the width from `--image`.
- If the width is not 512, the helper auto-resizes the image to width 512.
- The scaled height is rounded down to a multiple of 8 before editing.
- There is no separate `--width` flag; changing the input image is what matters.

Use `references/assets/kaori.jpg` to exercise the resize path.

## Local weights

If you have downloaded the base model and LoRA locally, pass existing filesystem paths instead of Hub ids. Missing paths fail at load time; the helper does not download or create local checkpoints.

```bash
python /path/to/ic-edit-skill/sub-skills/inference/scripts/run_icedit_inference.py \
  --mode normal \
  --image /path/to/ic-edit-skill/sub-skills/inference/references/assets/girl.png \
  --instruction "Make her hair dark green and her clothes checked." \
  --flux-path /path/to/flux.1-fill-dev \
  --lora-path /path/to/ICEdit-normal-LoRA
```

## CPU offload

For lower-VRAM CUDA machines, add:

```bash
--enable-model-cpu-offload
```

The README frames this as the practical fallback for roughly 24 GB-class cards.
Expect slower inference than the full GPU path.

## MoE edit

MoE is not standalone: use an ICEdit checkout whose `icedit/` directory is available, and pass that checkout explicitly.

```bash
python /path/to/ic-edit-skill/sub-skills/inference/scripts/run_icedit_inference.py \
  --mode moe \
  --repo-root /path/to/ICEdit-checkout \
  --image /path/to/ic-edit-skill/sub-skills/inference/references/assets/girl.png \
  --instruction "Make her hair dark green and her clothes checked." \
  --seed 42
```

If the checkout or its vendored package is missing, use `--mode normal` instead. `ICEDIT_REPO_ROOT` may be used instead of `--repo-root`.

## Output naming

- Default filename: the input basename, such as `girl.png`.
- Override with `--output-name result.png`.
- Save location: `--output-dir`, which defaults to the current directory.

## Bundled example inputs

- `references/assets/girl.png`: 512×768, good for a clean edit smoke test.
- `references/assets/boy.png`: 512×773, shows that height can stay uneven when width is already 512.
- `references/assets/kaori.jpg`: 2000×2000, useful for checking the automatic resize path.
