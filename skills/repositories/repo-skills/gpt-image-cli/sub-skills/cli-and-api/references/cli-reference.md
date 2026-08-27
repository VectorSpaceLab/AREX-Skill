# CLI reference

This reference covers the installable `gpt-image-cli` package and its `gpt-image` console command. It is safe to read/use without the source repository.

## Verified package surface

- Distribution name/version: `gpt-image-cli` / `0.2.0`.
- Python: requires `>=3.11`.
- Runtime dependencies: `openai>=1.55`, `python-dotenv>=1.0`.
- Import package: `gpt_image_cli`.
- Console script: `gpt-image = gpt_image_cli.cli:main`.
- Default model: `gpt-image-2`.
- Default size: `1024x1024`.
- Default moderation: `low`.
- Default quality in the CLI parser: `high`.

## Safe preflight

```bash
# Command availability.
command -v gpt-image || true
gpt-image --help

# Module availability if installed in the active Python environment.
python -m gpt_image_cli.cli --help

# Credential presence without printing the value.
test -n "${OPENAI_API_KEY:-}" && echo "OPENAI_API_KEY set" || echo "OPENAI_API_KEY not set"

# Bundled no-API helper.
python scripts/gpt_image_cli_helper.py preflight
```

Do not create `.env` files or write API keys unless the user explicitly asks. If a real call should not use local credentials, unset `OPENAI_API_KEY` and ensure no local env file is loaded for that run.

## Endpoint routing

| CLI trigger | SDK endpoint | Notes |
|---|---|---|
| No `-i/--image` | `client.images.generate(...)` | Text-to-image generation. `--moderation` is sent only on this route. |
| One or more `-i/--image` | `client.images.edit(...)` | Reference-image edit. Repeat `-i` for multi-reference edits. |
| `-i/--image` plus `-m/--mask` | `client.images.edit(...)` with `mask` | Mask inpainting. `--mask` without `--image` exits with bad-argument status. |

## Common commands

```bash
# Text -> image, explicit output.
gpt-image -p "a photorealistic convenience store at 10pm" \
  --size 1k --quality high -f store.png

# Cheap draft batch; n>1 produces suffixes such as _0, _1, ...
gpt-image -p "four clean logo directions for a bakery named Field & Flour" \
  --size portrait --quality low -n 4 -f logo.png

# Single-reference restyle/edit.
gpt-image -p "Make it a winter evening with heavy snowfall. Keep the board layout and camera angle." \
  -i chess.png --quality high -f chess-winter.png

# Multi-reference edit: describe each input by index in the prompt.
gpt-image -p "Image 1 is the person; Image 2 is the jacket. Put the jacket on the person, preserve identity and lighting." \
  -i person.png -i jacket.png --size portrait --quality medium -f styled-person.png

# Mask inpaint. Mask interpretation: opaque = keep, transparent = regenerate.
gpt-image -p "replace the sky with aurora, keep the landscape unchanged" \
  -i landscape.png -m sky_mask.png -f aurora.png

# WebP output with compression; align --format and filename extension yourself.
gpt-image -p "isometric chair, minimalist catalog render" \
  --format webp --compression 80 -f chair.webp
```

## Flags and defaults

| Flag | Values/default | Route | Operational notes |
|---|---|---|---|
| `-p`, `--prompt` | required string | both | Text prompt or edit instruction. For edits, state what changes and what must be preserved. |
| `-f`, `--file` | optional path | both | If omitted, the CLI auto-generates a timestamped filename. |
| `-i`, `--image` | repeatable path | edits | Presence of any image switches to the edits endpoint. Paths must exist. |
| `-m`, `--mask` | path | edits | Requires `--image`. Intended for alpha-channel PNG masks: opaque preserved, transparent regenerated. |
| `--model` | default `gpt-image-2` | both | `gpt-image-2` is the default model. |
| `--size` | default `1024x1024`; shortcuts below | both | Accepts shortcuts or literal pixel dimensions. |
| `--quality` | `auto`, `low`, `medium`, `high`; default `high` | both | Main cost/fidelity knob. Use `low` for drafts, `medium` for exploration, `high` for final/dense text. |
| `-n`, `--n` | integer, default `1` | both | Number of images. With `n>1`, output filenames are suffixed from `_0` upward. |
| `--background` | `auto`, `opaque`; omitted by default | both in CLI call surface | `opaque` disables transparency. Omitted means API-side default/auto behavior. |
| `--moderation` | `auto`, `low`; default `low` | generations | The CLI sends it on the generation route only. Use `auto` for stricter API-side default behavior. |
| `--input-fidelity` | `low`, `high`; omitted by default | edits | `gpt-image-2` rejects this parameter, so the CLI drops it locally for the default model. |
| `--format` | `png`, `jpeg`, `webp`; default `png` | both | Controls returned encoding. If `-f` is explicit, keep its extension consistent manually. |
| `--compression` | integer `0`-`100` | both | Intended for `jpeg`/`webp`; ignored for `png` by the API. |
| `--user` | string | both | Optional end-user identifier forwarded to OpenAI for abuse tracking. |

## Size shortcuts

The CLI resolves these shortcuts before calling the SDK:

| Shortcut | Literal size |
|---|---:|
| `1k` | `1024x1024` |
| `2k` | `2048x2048` |
| `4k` | `3840x2160` |
| `portrait` | `1024x1536` |
| `landscape` | `1536x1024` |
| `square` | `1024x1024` |
| `wide` | `2048x1152` |
| `tall` | `2160x3840` |

Literal sizes must satisfy the model/API constraints: each edge is a multiple of 16, long:short ratio no greater than 3:1, total pixels within the supported range, and maximum edge within API limits. Very large targets, including 4K-style shortcuts, can be more variable and may be rejected if the live API enforces a stricter edge limit.

## Output behavior

- If `-f/--file` is omitted, the CLI writes to `./fig/` when that directory exists; otherwise it writes to the current directory.
- Auto names are `YYYY-MM-DD-HH-MM-SS-<prompt-slug>.<extension>`.
- The default extension is `png`; `--format jpeg` or `--format webp` changes the auto extension.
- If `-f` is provided, the CLI uses that path exactly. It does not rewrite the suffix to match `--format`.
- For `-n 1`, exactly the requested path is written. For `-n > 1`, the stem is suffixed as `_0`, `_1`, and so on.
- Output parent directories are created automatically.

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Success; output path(s) are printed on stdout. |
| `1` | OpenAI API error/refusal or response did not contain image data. |
| `2` | Bad arguments or preflight failure before an API call, such as missing `OPENAI_API_KEY`, missing image/mask path, or `--mask` without `--image`. |

## Command-building helper

```bash
# Build without executing; prints endpoint mode and shell-quoted command.
python scripts/gpt_image_cli_helper.py build-command \
  -p "replace the shirt with the jacket from Image 2" \
  -i person.png -i jacket.png --size portrait --quality medium -f result.png

# Optional real execution. This can call the OpenAI API and may cost money.
python scripts/gpt_image_cli_helper.py build-command --execute \
  -p "a simple pencil sketch of a teapot" --quality low -f teapot.png
```
