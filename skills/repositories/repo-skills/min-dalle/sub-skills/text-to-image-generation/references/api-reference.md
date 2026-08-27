# API Reference: Python Text-to-Image Generation

This reference covers the Python `min_dalle.MinDalle` generation API. It intentionally excludes cache sizing, model download policy, CLI/UI wrappers, Colab UX, and hosted deployment surfaces.

## Core imports

```python
import torch
from PIL import Image
from min_dalle import MinDalle
```

Use `MinDalle` for in-process Python inference. Construction and generation can download or load model assets; plan those preconditions with the sibling model-assets/runtime sub-skill before running expensive calls.

## Verified constructor signature

```python
MinDalle(
    models_root: str = "pretrained",
    dtype: torch.dtype = torch.float32,
    device: str = None,
    is_mega: bool = True,
    is_reusable: bool = True,
    is_verbose=True,
)
```

Constructor semantics:

- `models_root`: root directory for tokenizer, DALL·E BART, and VQGAN detokenizer files. The implementation creates `dalle_bart_mega` or `dalle_bart_mini` plus `vqgan` subdirectories under this root. Missing files are downloaded from the min-dalle model repository.
- `dtype`: PyTorch dtype used to initialize the encoder/decoder and autocast generation. `torch.float32` is the safest default. `torch.float16` saves GPU memory. `torch.bfloat16` is intended for capable Ampere-class CUDA GPUs. Prefer `torch.float32` on CPU unless the environment proves otherwise.
- `device`: `None` auto-selects `'cuda'` when `torch.cuda.is_available()` is true, else `'cpu'`. The README documents `cuda` and `cpu`; other device strings are not part of the verified contract.
- `is_mega`: `True` uses the larger mega model settings (`24` layers, `32` attention heads, wider embeddings and vocabs). `False` uses the smaller mini settings (`12` layers, `16` heads) and lower resource demand.
- `is_reusable`: `True` initializes encoder, decoder, and detokenizer in the constructor and keeps them resident for repeated calls. `False` initializes and deletes those modules during generation phases, retaining only the tokenizer between calls; this can reduce peak residency for one-shot runs at the cost of repeated loading.
- `is_verbose`: prints initialization/generation stage messages when true.

Important construction side effects:

- `init_tokenizer()` always runs during construction. It issues a small model-repository request and downloads tokenizer files if they are absent.
- When `is_reusable=True`, constructor initialization also downloads/loads encoder, decoder, and detokenizer weights if absent.
- When `is_reusable=False`, full weights are loaded later by generation and detokenization paths.

## Common generation arguments

The stream-generating core API has this verified signature:

```python
generate_raw_image_stream(
    text: str,
    seed: int,
    grid_size: int,
    progressive_outputs: bool = False,
    is_seamless: bool = False,
    temperature: float = 1,
    top_k: int = 256,
    supercondition_factor: int = 16,
    is_verbose: bool = False,
) -> Iterator[torch.FloatTensor]
```

Argument semantics:

- `text`: prompt string. The tokenizer demojizes text, lowercases it, drops non-ASCII characters, byte-pair encodes words, adds start/end tokens, and truncates to `64` text tokens.
- `seed`: a positive value calls `torch.manual_seed(seed)` before image-token sampling. `0` or negative values do not set a manual seed.
- `grid_size`: number of images per side. The model samples `grid_size ** 2` images, each represented by `256` image tokens. The final grid image is `grid_size * 256` pixels on each side.
- `progressive_outputs`: when true, raw/PIL/tensor stream APIs detokenize and yield every `32` image tokens plus the final 256-token result. When false, they yield only the final result. Non-stream wrappers force this to false.
- `is_seamless`: detokenizes tiled token grids as one seamless token-space image rather than stitching already-rendered pixel images.
- `temperature`: positive sampler temperature applied after subtracting the largest logit. Lower values reduce diversity; higher values increase diversity/noise. Do not use `0` or negative values.
- `top_k`: number of highest-probability token logits retained before sampling. The implementation indexes `top_k - 1` into a `16384`-token image vocabulary slice, so use `1 <= top_k <= 16384`. Default examples use `128` or `256`.
- `supercondition_factor`: classifier-free guidance-style mix of unconditional and conditional logits: `unconditional * (1 - factor) + conditional * factor`. Higher values usually improve prompt agreement but reduce variety; defaults/examples center around `16` and sometimes `32`.
- `is_verbose`: prints tokenization, encoding, and detokenization messages.

## Output methods and contracts

### `generate_raw_image_stream`

```python
model.generate_raw_image_stream(
    text="Dali painting of WALL·E",
    seed=-1,
    grid_size=3,
    progressive_outputs=True,
    is_seamless=False,
    temperature=1,
    top_k=256,
    supercondition_factor=16,
    is_verbose=False,
)
```

Returns an iterator of grid `torch.FloatTensor` images. Each yielded tensor is shaped approximately `(grid_size * 256, grid_size * 256, 3)` with values clipped to `[0, 255]`. It remains a floating-point tensor; convert to `uint8` CPU NumPy before PIL saving.

### `generate_image_stream`

Verified signature:

```python
generate_image_stream(self, *args, **kwargs) -> Iterator[PIL.Image.Image]
```

Wraps `generate_raw_image_stream()`, converts each yielded grid tensor to `torch.uint8`, moves it to CPU, converts to NumPy, and yields a PIL `Image`. Use this for notebook/progressive display or saving progressive grid PNGs.

### `generate_images_stream`

Verified signature:

```python
generate_images_stream(self, *args, **kwargs) -> Iterator[torch.FloatTensor]
```

Wraps `generate_raw_image_stream()` and reshapes each yielded grid tensor into individual images with shape:

```python
(grid_size ** 2, 256, 256, 3)
```

Important: this method reads `grid_size` from `kwargs["grid_size"]`. Call it with `grid_size=...`, not with positional arguments. The tensor remains floating point and may reside on the generation device.

### `generate_image`

Verified signature:

```python
generate_image(self, *args, **kwargs) -> PIL.Image.Image
```

Returns the first/final PIL grid image from `generate_image_stream(..., progressive_outputs=False)`. Do not pass `progressive_outputs` to this wrapper; use `generate_image_stream()` when progressive frames are needed.

### `generate_images`

Verified signature:

```python
generate_images(self, *args, **kwargs) -> PIL.Image.Image
```

The annotation says `PIL.Image.Image`, but the implementation returns the first/final tensor batch from `generate_images_stream(..., progressive_outputs=False)`. Treat the actual result as:

```python
torch.FloatTensor  # shape: (grid_size ** 2, 256, 256, 3), values 0..255
```

As with `generate_images_stream()`, pass `grid_size` as a keyword argument and do not pass `progressive_outputs` to the non-stream wrapper.

### `image_grid_from_tokens`

Verified signature:

```python
image_grid_from_tokens(
    image_tokens: torch.LongTensor,
    is_seamless: bool,
    is_verbose: bool = False,
) -> torch.FloatTensor
```

Detokenizes image-token tensors into a grid tensor. Expected `image_tokens` shape is `(grid_size ** 2, 256)`, excluding the initial image start token. This is mainly useful for debugging token-level generation or custom sampling. With `is_reusable=False`, the method deletes the decoder reference, initializes the detokenizer for this phase, and deletes the detokenizer afterward.

## Evidence-backed output expectations

Observed generated-example artifacts confirm these contracts:

- Single-image examples are RGB JPEGs at `256×256`, consistent with `grid_size=1`.
- `4×4` grid examples are RGB JPEGs at `1024×1024`, consistent with `grid_size * 256` pixels.
- Larger temperature-comparison examples are RGB JPEGs at `1280×1280`, consistent with `grid_size=5`.
- The progressive WALL·E example is an animated GIF with `8` frames, matching one frame every `32` decode tokens over `256` total image tokens.

See [generation-workflows.md](generation-workflows.md) for recipes and [troubleshooting.md](troubleshooting.md) for common failures.
