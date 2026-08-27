# CLI Reference

min(DALL·E) exposes a repository script for command-line generation, but the package metadata does not define an installed console entry point. Future agents should use this sub-skill's bundled CLI template instead of assuming a `min-dalle` shell command exists.

## Bundled safe CLI template

Use `scripts/min_dalle_cli_template.py` from this sub-skill for portable command construction. It defaults to dry run, prints the planned constructor/generation call, and does not import `MinDalle`, download model assets, or run inference unless `--run` is supplied.

No-download checks:

```bash
python scripts/min_dalle_cli_template.py --help
python scripts/min_dalle_cli_template.py --text "artificial intelligence" --no-mega --top-k 256
```

Generation after explicit approval:

```bash
python scripts/min_dalle_cli_template.py \
  --run \
  --text "artificial intelligence" \
  --no-mega \
  --grid-size 1 \
  --models-root pretrained \
  --image-path generated.png \
  --top-k 256 \
  --device cpu \
  --dtype float32
```

## Source script behavior distilled

The upstream command-line script's public behavior is captured below so the original checkout is not needed.

| Capability | Bundled template option | Upstream source flag/default | Behavior |
|---|---|---|---|
| Choose model variant | `--mega` / `--no-mega` | `--mega` / `--no-mega`, default `--no-mega` | Selects Mega or Mini model settings. The bundled template keeps the same default as the upstream script: Mini. |
| Precision shortcut | `--fp16` or `--dtype` | `--fp16`, default false | Upstream maps `--fp16` to `torch.float16`, otherwise `torch.float32`. The bundled helper also accepts explicit `--dtype float32|float16|bfloat16`. |
| Prompt | `--text` | `--text`, default `Dali painting of WALL·E` | Prompt passed to `generate_image`. Text is normalized by the tokenizer during generation. |
| Seed | `--seed` | `--seed`, default `-1` | Positive seeds call `torch.manual_seed`; negative/zero values leave sampling random. |
| Grid size | `--grid-size` | `--grid-size`, default `1` | Produces `grid_size ** 2` images in a grid. |
| Output path | `--image-path` | `--image-path`, default `generated` | If the path is a directory, save `generated.png` inside it. If it lacks `.png`, append `.png`. |
| Model cache | `--models-root` | `--models-root`, default `pretrained` | Directory for tokenizer/model assets. |
| Sampling top-k | `--top-k` | `--top_k`, default `256` | The source uses underscore spelling. The bundled helper uses normal hyphen spelling and documents the mapping. |
| Device | `--device` | implicit auto-select in `MinDalle` | The upstream script does not expose a device flag. The bundled helper exposes one for safer CPU/CUDA planning. |
| Run safety | `--dry-run` / `--run` | none | The source script immediately constructs a model and may download weights. The bundled helper requires `--run` for side effects. |

## Save and ASCII preview behavior

The upstream script saves a generated PIL image and then prints an ASCII preview:

- If the requested path is an existing directory, it writes `generated.png` inside that directory.
- If the requested path does not end with `.png`, it appends `.png`.
- The ASCII preview converts the image to grayscale, resizes to a wide text grid, and maps pixel intensity to characters `.,;/IOX`.

The bundled template preserves this behavior after `--run`, and its dry-run mode prints the resolved output path before any model construction.

## CLI boundaries

- The CLI generates one PIL grid image through `MinDalle.generate_image`; it does not expose progressive outputs, tensor batches, Replicate streaming, or GUI controls.
- Use `../text-to-image-generation/SKILL.md` when the task needs stream APIs, tensor output, or custom Python integration.
- Use `../model-assets-and-runtime/SKILL.md` when the task is primarily model-cache, dtype, device, or weight-download planning.
