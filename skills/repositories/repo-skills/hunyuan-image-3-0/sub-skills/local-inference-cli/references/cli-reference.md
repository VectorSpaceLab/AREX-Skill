# Local CLI Reference

This sub-skill centers on the local generation command surface originally represented by the repo CLI. The generated skill bundles `scripts/run_hunyuan_image_generation.py` as a self-contained runner and `scripts/local_inference_cli_dry_run.py` as a safe command renderer.

## Canonical entry surfaces

- `python scripts/run_hunyuan_image_generation.py ...` for skill-owned local generation with an installed package and a local checkpoint.
- `python scripts/local_inference_cli_dry_run.py ...` for safe rendering or validation without loading weights.
- The demo shell recipes are reference-only command templates. Mirror their flag sets in your own command rather than sourcing them directly.

## Checkpoint naming conventions

Use a local directory path for `--model-id`. The parser checks that the path exists before loading.

Recommended local directory names:

| Checkpoint family | Local directory example | Notes |
|---|---|---|
| Base / text-to-image | `./HunyuanImage-3` | Use this for the base checkpoint. |
| Instruct / editing | `./HunyuanImage-3-Instruct` | Use this for `think_recaption`, `recaption`, and multi-image editing. |
| Distilled instruct | `./HunyuanImage-3-Instruct-Distil` | Same workflow as instruct, but with the 8-step distil recipe. |

When downloading from Hugging Face, rename the local directory to a dot-free path before using it as `--model-id`.

## Flag matrix

### Required inputs and outputs

| Flag | Meaning | Default / behavior | Notes |
|---|---|---|---|
| `--prompt` | Main text prompt | Required | The parser rejects empty prompts. |
| `--model-id` | Local checkpoint path | Required | Must exist before loading. |
| `--image` | One image or comma-separated image paths | Optional in the parser; required for editing workflows | The parser trims whitespace and drops empty segments. |
| `--save` | Output image path | `image.png` | Parent directories are created automatically. |

### Task and prompt control

| Flag | Meaning | Default / behavior | Notes |
|---|---|---|---|
| `--bot-task` | Task mode | Loaded from model config when omitted | Parser choices: `image`, `auto`, `recaption`, `think_recaption`. The documented local recipes use `image` for base and `think_recaption` for instruct / distil. |
| `--use-system-prompt` | System-prompt mode | Loaded from model config when omitted | Parser choices: `None`, `dynamic`, `en_vanilla`, `en_recaption`, `en_think_recaption`, `en_unified`, `custom`. |
| `--system-prompt` | Custom system prompt | Empty / unused unless `--use-system-prompt custom` | Required when `--use-system-prompt custom`. |
| `--rewrite` | DeepSeek-based prompt rewrite branch | Disabled unless requested | Requires Tencent Cloud credentials. See troubleshooting for the current parser mismatch warning. |
| `--infer-align-image-size` | Align output size to input image size | Disabled unless requested | Most useful for TI2I and multi-image editing. |

### Sampling, size, and reproducibility

| Flag | Meaning | Default / behavior | Notes |
|---|---|---|---|
| `--seed` | Random seed | `None` | Pair with `--reproduce` when you want deterministic output. |
| `--reproduce` | Enable deterministic settings | Off | The code seeds Python, NumPy, and PyTorch and enables deterministic CUDA settings. |
| `--diff-infer-steps` | Diffusion inference steps | `50` | Distil recipes use `8`. |
| `--image-size` | Target image size | `auto` | Use `auto`, `1024x1024`, or a ratio form such as `16:9`. The processor snaps explicit sizes to the nearest preset. |
| `--max_new_tokens` | Maximum text tokens before image generation | `2048` | Mostly relevant to the reasoning / recaption stage. |
| `--verbose` | Verbosity level | `2` in the parser | Higher values print more inference detail. |

### Backend and performance

| Flag | Meaning | Default / behavior | Notes |
|---|---|---|---|
| `--attn-impl` | Attention implementation | `sdpa` | Parser choices: `sdpa`, `flash_attention_2`. FlashAttention is optional. |
| `--moe-impl` | MoE implementation | `eager` | Parser choices: `eager`, `flashinfer`. FlashInfer is optional. |
| `--use-taylor-cache` | Enable Taylor Cache | Off | Passes through to the model. |
| `--taylor-cache-interval` | Taylor Cache interval | `5` | Only matters when Taylor Cache is enabled. |
| `--taylor-cache-order` | Taylor Cache order | `2` | Only matters when Taylor Cache is enabled. |
| `--taylor-cache-enable-first-enhance` | First-enhance pass | Off | Optional Taylor Cache tuning. |
| `--taylor-cache-first-enhance-steps` | First-enhance steps | `3` | Should stay above `2` if enabled. |
| `--taylor-cache-enable-tailing-enhance` | Tailing-enhance pass | Off | Optional Taylor Cache tuning. |
| `--taylor-cache-tailing-enhance-steps` | Tailing-enhance steps | `1` | Optional Taylor Cache tuning. |
| `--taylor-cache-low-freqs-order` | Low-frequency order | `2` | Optional Taylor Cache tuning. |
| `--taylor-cache-high-freqs-order` | High-frequency order | `2` | Optional Taylor Cache tuning. |

## Recommended command shapes

### Base text-to-image

- `--model-id ./HunyuanImage-3`
- `--bot-task image`
- `--image-size 1024x1024`
- `--save ./outputs/image.png`
- Optional reproducibility: `--seed <n> --reproduce`
- Optional speed-up: `--moe-impl flashinfer` if the accelerator is installed

### Instruct / TI2I

- `--model-id ./HunyuanImage-3-Instruct`
- `--prompt "..."`
- `--image <one-or-more comma-separated images>`
- `--bot-task think_recaption`
- `--use-system-prompt en_unified`
- `--image-size auto`
- `--infer-align-image-size`
- `--save ./outputs/edit.png`

### Distilled instruct

- Same as instruct / TI2I, but use `./HunyuanImage-3-Instruct-Distil` and `--diff-infer-steps 8`.

## Rewrite warning branch

The local CLI can ask Tencent Cloud's DeepSeek service to rewrite the prompt before generation.

Practical rules:

1. `DEEPSEEK_KEY_ID` and `DEEPSEEK_KEY_SECRET` must be present.
2. The branch is optional and should be treated as experimental in this snapshot.
3. The original source snapshot references `args.sys_deepseek_prompt`, which is not defined by that parser; the bundled runner adds `--sys-deepseek-prompt` so the branch is explicit.
4. Use the safe helper to surface credential or branch issues before launching GPU work.

## Router hints

- For system-prompt behavior and recaption semantics, route to `prompt-and-image-conditioning`.
- For model construction and public API signatures, route to `core-apis-and-architecture`.
- For vLLM payloads or server/client commands, route to `vllm-serving`.
