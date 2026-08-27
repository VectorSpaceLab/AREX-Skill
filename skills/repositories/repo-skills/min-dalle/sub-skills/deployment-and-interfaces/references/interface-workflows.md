# Interface Workflows

This reference covers min(DALL·E)'s documented public interfaces beyond direct in-process API calls: notebook/Colab use, Tkinter UI behavior, and Replicate/Cog deployment. It distills the source evidence into portable guidance; no original checkout files are required at runtime.

## Colab and notebook pattern

The notebook workflow is:

1. Check GPU visibility with a notebook shell command such as `nvidia-smi`.
2. Install `min-dalle` in the notebook runtime.
3. Import `torch`, `IPython.display.display`, `IPython.display.update_display`, and `MinDalle`.
4. Choose a dtype string from `float32`, `float16`, or `bfloat16`, then pass `getattr(torch, dtype)` into `MinDalle`.
5. Construct a reusable Mega model on CUDA for repeated prompts.
6. Call `generate_image_stream(..., progressive_outputs=True)` and update the same display id for each yielded image.

Notebook display skeleton:

```python
from IPython.display import display, update_display
import torch
from min_dalle import MinDalle

model = MinDalle(
    dtype=torch.float32,
    device="cuda",
    is_mega=True,
    is_reusable=True,
)

image_stream = model.generate_image_stream(
    text="Dali painting of WALL-E",
    seed=-1,
    grid_size=3,
    progressive_outputs=True,
    is_seamless=False,
    temperature=1.0,
    top_k=128,
    supercondition_factor=16,
)

is_first = True
for image in image_stream:
    (display if is_first else update_display)(image, display_id=1)
    is_first = False
```

Use the text-to-image generation sub-skill for API details and the runtime sub-skill before increasing grid size, switching dtype, or depending on CUDA.

## Tkinter UI behavior

The desktop UI flow is interactive and requires a display server:

- It first shows a choice between Mega and Mini.
- It constructs a reusable `MinDalle` model with `models_root="./pretrained"`.
- It displays a 2x2 image grid placeholder, prompt field, temperature field, top-k field, supercondition factor field, seamless checkbox, and Generate/Save/Quit buttons.
- Generation uses `generate_image_stream(..., grid_size=2, seed=-1, progressive_outputs=True)` and updates the label with each PIL image.
- Save writes the final generated image to `generated/out.png`.

Do not run GUI workflows in headless automation unless a display server is configured and the user explicitly wants interactive behavior. Prefer the bundled CLI template or direct API recipes for automated tasks.

## Replicate/Cog predictor behavior

The Replicate predictor wraps a reusable Mega model on CUDA and yields generated image paths from `predict(...)`.

Setup behavior:

- The predictor setup constructs `MinDalle(is_mega=True, is_reusable=True, dtype=torch.float32, device="cuda")`.
- CUDA and GPU are assumed.
- The Cog configuration evidence uses Python 3.10, CUDA 11.5.1, system packages `libgl1-mesa-glx` and `libglib2.0-0`, package pins `min-dalle==0.4.5` and `emoji==1.7.0`, and installs `torch==1.12.0+cu116` from the PyTorch wheel index. Treat these pins as deployment evidence for that Cog image, not as the current package's base install requirements.

Predictor inputs and defaults:

| Input | Default | Constraints / meaning |
|---|---:|---|
| `text` | `Dali painting of WALL·E` | Prompt string. |
| `save_as_png` | `False` | Final frame uses PNG only when true; otherwise JPEG. |
| `progressive_outputs` | `True` | Yields intermediate frames when true. |
| `seamless` | `False` | Passed to `is_seamless`. |
| `grid_size` | `5` | Constrained from 1 to 9 in the Cog input schema. |
| `temperature` | `4` | Constrained from 0.01 to 16. |
| `top_k` | `64` | Choices are powers of two from `1` through `16384`. |
| `supercondition_factor` | `16` | Choices are powers of two from `4` through `64`. |

Output behavior:

- Each yielded output path is created under a temporary directory.
- The output basename is a sanitized version of prompt text: emoji demojized, lowercased, ASCII-only, letters/spaces kept, truncated to 64 characters, spaces collapsed to hyphens, and `blank` used if no letters remain.
- Intermediate progressive frames append `-iter-N`.
- The final frame uses `.png` only when `save_as_png=True`; otherwise it uses `.jpg`.
- The implementation treats `i == 8` as the final progressive frame, consistent with one frame every 32 decode tokens across 256 tokens.

Use `scripts/replicate_filename_sanitize.py` to preview the basename without Cog, CUDA, or model loading:

```bash
python scripts/replicate_filename_sanitize.py --text "Dali painting of WALL-E"
python scripts/replicate_filename_sanitize.py --self-test
```

## Deployment boundaries

- Do not use the CPU inspection environment as evidence that a Cog/CUDA deployment works.
- A local script can mimic input validation and filename rules, but true Replicate verification requires Cog plus a CUDA runtime and model downloads.
- If users want a production API service unrelated to the provided Cog predictor, use these inputs and cache/runtime rules as a starting point but design service hardening separately.
