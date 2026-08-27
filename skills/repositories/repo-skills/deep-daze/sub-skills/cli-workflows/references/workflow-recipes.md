# CLI workflow recipes

Use these recipes as starting points. They intentionally keep early runs small because `imagine` performs iterative optimization and may download CLIP weights on first use. Run commands from the directory where images, progress frames, GIFs, videos, and `story_transitions.txt` should be written.

## Build first, run second

The bundled builder prints commands and validates local file inputs without starting generation:

```bash
python scripts/build_imagine_command.py --prompt "a tiny cabin beside a foggy lake"
```

Example output shape:

```bash
imagine 'a tiny cabin beside a foggy lake' --epochs=1 --iterations=10 --save_every=5 --image_width=256 --num_layers=8 --hidden_size=128 --batch_size=1 --gradient_accumulate_every=4 --save_progress=True --open_folder=False --save_date_time=True --overwrite=False --model_name=ViT-B/32 --optimizer=AdamP
```

Copy the printed command into the desired output directory. Keep `--open_folder=False` on headless machines. Keep `--save_date_time=True` when you want to avoid overwrite prompts without clobbering existing files.

## Text prompt: safe smoke run

```bash
imagine "a small house in a misty forest" \
  --epochs=1 \
  --iterations=10 \
  --save_every=5 \
  --image_width=256 \
  --num_layers=8 \
  --hidden_size=128 \
  --batch_size=1 \
  --gradient_accumulate_every=4 \
  --save_progress=True \
  --open_folder=False \
  --save_date_time=True
```

Expected artifacts:

- Timestamped final/current image ending in `a_small_house_in_a_misty_forest.jpg`.
- Timestamped progress frames when progress saves occur. The first progress save updates the base `.jpg`; later sequence frames end in values such as `a_small_house_in_a_misty_forest.000001.jpg`.

## Text prompt: low-memory exploratory run

```bash
imagine "a crystalline tree under a violet sunrise" \
  --epochs=1 \
  --iterations=50 \
  --save_every=10 \
  --image_width=256 \
  --num_layers=16 \
  --batch_size=1 \
  --gradient_accumulate_every=16 \
  --save_progress=True \
  --open_folder=False \
  --save_date_time=True
```

Use this when the machine is CPU-only, has limited GPU memory, or when model/cache readiness is not yet proven. Increase `iterations`, `epochs`, `image_width`, or `num_layers` only after the short run succeeds.

## Text prompt: deeper SIREN network

Two equivalent command styles are useful:

```bash
imagine "stranger in strange lands" --deeper=True --open_folder=False --save_date_time=True
```

or explicit layers:

```bash
imagine "stranger in strange lands" --num_layers=32 --open_folder=False --save_date_time=True
```

`--deeper=True` sets the layer count to 32 regardless of the `--num_layers` value. Prefer explicit `--num_layers` in automation so the command records the exact value being requested.

## Image target only

Use `--img` when the objective is CLIP's interpretation of an image rather than a text prompt:

```bash
imagine --img=inputs/target_landscape.jpg \
  --epochs=1 \
  --iterations=25 \
  --save_every=5 \
  --image_width=256 \
  --batch_size=1 \
  --gradient_accumulate_every=8 \
  --save_progress=True \
  --open_folder=False \
  --save_date_time=True
```

Expected base filename comes from the input image stem, not from a prompt.

## Text plus image target

Supplying both text and `--img` averages the text and image CLIP encodings:

```bash
imagine "a psychedelic watercolor interpretation" \
  --img=inputs/reference_photo.jpg \
  --epochs=1 \
  --iterations=50 \
  --save_every=10 \
  --image_width=256 \
  --batch_size=1 \
  --gradient_accumulate_every=16 \
  --save_progress=True \
  --open_folder=False \
  --save_date_time=True
```

Use this for blended conditioning: the prompt steers style/content while the target image contributes visual semantics.

## Start-image priming

Use `--start_image_path` when the generator should first fit an initial image, then move toward the text/image CLIP objective:

```bash
imagine "a clear night sky filled with stars" \
  --start_image_path=inputs/cloudy_night_sky.jpg \
  --start_image_train_iters=25 \
  --start_image_lr=3e-4 \
  --epochs=1 \
  --iterations=50 \
  --save_every=10 \
  --image_width=256 \
  --batch_size=1 \
  --gradient_accumulate_every=16 \
  --save_progress=True \
  --open_folder=False \
  --save_date_time=True
```

Start-image priming is not the same as `--img`:

- `--start_image_path` initializes the SIREN generator from the image and then discards the priming image.
- `--img` remains part of the optimization target through CLIP.
- They can be combined when you need both priming and CLIP image conditioning.

## Combined text, image target, and start-image priming

```bash
imagine "a luminous botanical illustration" \
  --img=inputs/target_flower.jpg \
  --start_image_path=inputs/initial_canvas.jpg \
  --start_image_train_iters=20 \
  --epochs=1 \
  --iterations=50 \
  --save_every=10 \
  --image_width=256 \
  --batch_size=1 \
  --gradient_accumulate_every=16 \
  --save_progress=True \
  --open_folder=False \
  --save_date_time=True
```

Use the builder to validate both files before running:

```bash
python scripts/build_imagine_command.py \
  --prompt "a luminous botanical illustration" \
  --img inputs/target_flower.jpg \
  --start-image inputs/initial_canvas.jpg \
  --preset low-vram
```

## Story mode for long prompts

Normal text mode is bounded by CLIP's 77-token context. Story mode creates a changing prompt window across epochs and is the CLI path for long prose:

```bash
imagine "first scene. second scene. third scene. fourth scene." \
  --create_story=True \
  --story_separator=. \
  --save_progress=True \
  --save_video=True \
  --iterations=25 \
  --save_every=5 \
  --image_width=256 \
  --batch_size=1 \
  --gradient_accumulate_every=16 \
  --open_folder=False \
  --save_date_time=True
```

Notes:

- With `--story_separator=.`, each separator-delimited chunk becomes an epoch. If the separator is absent, it is ignored.
- Without a separator, the first epoch uses `--story_start_words`, then each epoch adds `--story_words_per_epoch` words while trimming old words to fit the CLIP context.
- Keep `--save_progress=True`; otherwise transitions are hard to inspect and GIF/video creation has no frame set.
- Story mode writes `story_transitions.txt` in the output directory.

## Progress frames, GIFs, and MP4 videos

Progress frames:

```bash
imagine "glowing clouds over a city" \
  --epochs=1 \
  --iterations=40 \
  --save_every=5 \
  --save_progress=True \
  --open_folder=False \
  --save_date_time=True
```

GIF:

```bash
imagine "glowing clouds over a city" \
  --epochs=1 \
  --iterations=40 \
  --save_every=5 \
  --save_progress=True \
  --save_gif=True \
  --open_folder=False \
  --save_date_time=True
```

MP4:

```bash
imagine "glowing clouds over a city" \
  --epochs=1 \
  --iterations=40 \
  --save_every=5 \
  --save_progress=True \
  --save_video=True \
  --open_folder=False \
  --save_date_time=True
```

GIF/MP4 creation happens after training and depends on saved progress frames. If no frames match the base output name, animation creation cannot produce useful output.

## Avoiding overwrite prompts

The CLI asks before replacing an existing final image when `--overwrite=False` and the final filename already exists. For non-interactive runs choose one of these patterns:

```bash
# Preserve old outputs by making new timestamped names.
imagine "silver birds over black sand" --save_date_time=True --open_folder=False

# Intentionally replace the existing final/current image.
imagine "silver birds over black sand" --overwrite=True --open_folder=False
```

Prefer timestamping unless the task explicitly asks to update a fixed filename.

## Resource escalation checklist

1. Start with `smoke` or manually small flags: `epochs=1`, `iterations=10`, `image_width=256`, `batch_size=1`.
2. Confirm CLIP model availability and that output files are produced.
3. Increase `iterations` before increasing `image_width`.
4. Increase `num_layers` or use `--deeper=True` only when memory is stable.
5. Increase `batch_size` only when GPU memory permits; compensate with `gradient_accumulate_every` when batch size is low.
6. For final quality runs, record `seed`, `model_name`, resource flags, prompt, and output directory in the task notes.
