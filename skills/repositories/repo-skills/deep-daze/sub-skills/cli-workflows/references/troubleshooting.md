# CLI troubleshooting

This guide focuses on failures at the `imagine` command-line layer. For runtime setup, CLIP cache, device selection, dependency, or hardware diagnosis, route to [../../runtime-and-models/SKILL.md](../../runtime-and-models/SKILL.md). For direct Python API customization, route to [../../python-api/SKILL.md](../../python-api/SKILL.md).

## Prompt exceeds CLIP's 77-token context

Symptoms:

- Tokenization or text-encoding errors.
- A long paragraph appears to ignore early or late content.
- A normal prompt works, but a poem/story fails or gives unrelated output.

Recovery:

1. Shorten the normal prompt. The limit is CLIP tokens, not words; punctuation and uncommon words can split into multiple tokens.
2. Use story mode for long prose:

   ```bash
   imagine "first scene. second scene. third scene." \
     --create_story=True \
     --story_separator=. \
     --save_progress=True \
     --save_every=5 \
     --open_folder=False \
     --save_date_time=True
   ```

3. If using `--story_separator`, ensure that separator is actually present in the text. If absent, the CLI ignores it and falls back to word-window progression.
4. Do not pass text that consists only of separators; story mode exits because it needs words or phrases between separators.
5. Inspect `story_transitions.txt` in the output directory to see which text window was optimized at each transition.

## Missing `--img` or `--start_image_path` files

Symptoms:

- Image-only or text+image command fails while loading the target image.
- Start-image priming aborts with an assertion that the file does not exist.
- Relative paths work in one shell but fail in another.

Recovery:

1. Run `imagine` from the directory that makes relative input paths valid, or use absolute input paths if the task permits them in the private command invocation.
2. Validate files before running generation:

   ```bash
   python scripts/build_imagine_command.py --img inputs/target.jpg --preset smoke
   python scripts/build_imagine_command.py --prompt "night sky" --start-image inputs/prime.jpg --preset smoke
   ```

3. Use readable JPG or PNG inputs.
4. Remember the difference:
   - `--img=PATH` is a CLIP optimization target.
   - `--start_image_path=PATH` primes the generator before the target objective.

## Overwrite prompt blocks automation

Symptom:

```text
Imagined image already exists, do you want to overwrite? (y/n)
```

Recovery:

- Preserve existing outputs with timestamped names:

  ```bash
  imagine "prompt" --save_date_time=True --open_folder=False
  ```

- Or intentionally replace the final/current image:

  ```bash
  imagine "prompt" --overwrite=True --open_folder=False
  ```

- For batch/non-interactive jobs, do not leave collision behavior implicit. Choose timestamping or overwrite explicitly.

## `open_folder` fails or hangs on a headless system

Symptoms:

- `xdg-open` errors on Linux servers.
- Desktop file browser cannot launch over SSH, CI, containers, or notebooks.
- The run appears noisy at startup even though generation continues.

Recovery:

```bash
imagine "prompt" --open_folder=False
```

The bundled command builder sets `--open_folder=False` by default.

## Progress frames, GIF, or video not created

Symptoms:

- Final image exists but there are no sequence frames.
- `--save_gif=True` or `--save_video=True` produces no useful animation.
- MP4 writing fails at the end of the run.

Recovery:

1. Ensure progress saving is enabled:

   ```bash
   --save_progress=True
   ```

2. Use a positive `--save_every` that is smaller than or comparable to `--iterations`; otherwise there may be too few frames.
3. For GIF:

   ```bash
   --save_progress=True --save_gif=True
   ```

4. For MP4:

   ```bash
   --save_progress=True --save_video=True
   ```

5. MP4 support depends on the available image/video writer stack. If MP4 fails, retry with `--save_gif=True` or install the required video writer in the runtime environment.
6. With `--save_date_time=True`, progress frame names include timestamps; this is expected.

## CLIP model download or network failure

Symptoms:

- First run stalls or fails while downloading a `.pt` model.
- Checksum mismatch or partial cache file warnings.
- `RuntimeError: Model ... not found; available models = ...`.

Recovery:

1. Confirm `--model_name` is one of: `RN50`, `RN101`, `RN50x4`, `ViT-B/32`, `ViT-L/14`.
2. Prefer the default `--model_name=ViT-B/32` for portable commands.
3. Retry after network/cache readiness is handled by [../../runtime-and-models/SKILL.md](../../runtime-and-models/SKILL.md).
4. If using a local checkpoint path as `model_name`, verify that path privately before running; do not bake machine-specific checkpoint paths into reusable recipes.

## CPU/GPU slowness or out-of-memory

Symptoms:

- CPU runs take a very long time.
- CUDA out-of-memory errors.
- The process appears to make progress but each iteration is slow.

Recovery sequence:

1. Use a smoke or low-memory command first:

   ```bash
   imagine "prompt" \
     --epochs=1 \
     --iterations=10 \
     --image_width=256 \
     --num_layers=8 \
     --hidden_size=128 \
     --batch_size=1 \
     --gradient_accumulate_every=4 \
     --open_folder=False \
     --save_date_time=True
   ```

2. Lower `--image_width` before lowering prompt complexity.
3. Lower `--batch_size` and raise `--gradient_accumulate_every` to maintain effective accumulation.
4. Lower `--num_layers` or avoid `--deeper=True` on constrained memory.
5. Reduce `--iterations` and `--epochs` until setup is proven.
6. Confirm hardware/backend setup in [../../runtime-and-models/SKILL.md](../../runtime-and-models/SKILL.md) before scheduling expensive generation.

## Flag spelling and value types

Symptoms:

- Fire reports an unexpected flag.
- A boolean flag is interpreted incorrectly.
- A model name with `/` or a prompt with punctuation is parsed strangely.

Recovery:

- Use snake_case flag names from the CLI signature: `--num_layers`, `--start_image_path`, `--save_progress`, `--open_folder`.
- Use equals form for reliability: `--flag=value`.
- Use explicit booleans: `True` or `False`.
- Quote prompts and values with spaces:

  ```bash
  imagine "a house in the forest" --story_separator="."
  ```

- If a hyphenated flag from an old recipe fails, convert it to snake_case. Example: `--num-layers` -> `--num_layers`.
- Keep `--do_cutout=True` unless intentionally testing a custom augmentation behavior.

## Optimizer or model name mistakes

Symptoms:

- Invalid optimizer causes a later failure because no optimizer was configured.
- Invalid model name raises a model-not-found error.
- Larger CLIP model runs much slower or uses more memory.

Recovery:

- Supported optimizer names in the implementation are `AdamP`, `Adam`, and `DiffGrad`; the CLI default is `AdamP`.
- Supported built-in CLIP model names are `RN50`, `RN101`, `RN50x4`, `ViT-B/32`, and `ViT-L/14`; the CLI default is `ViT-B/32`.
- Quote or equals-bind model names in generated shell commands:

  ```bash
  --model_name=ViT-B/32
  ```

- When changing models, re-run a short smoke command before committing to a long optimization.

## JIT-related message

Symptom:

```text
Setting jit to False because torch version is not 1.7.1.
```

Recovery:

No CLI change is usually needed. The runtime automatically disables JIT CLIP loading unless the torch version is compatible. If a task specifically requires model/runtime tuning, route to [../../runtime-and-models/SKILL.md](../../runtime-and-models/SKILL.md).

## Start-image priming runs but final image ignores the start image

Causes and recovery:

- `--start_image_train_iters` may be too low; increase gradually, for example from `25` to `50` or `100`.
- The text/image CLIP objective may overpower the primed representation during later optimization; use shorter exploratory runs and inspect progress frames.
- If you intended the image to remain a target throughout training, also pass it with `--img=PATH`.

## Story mode produces too few or too many epochs

Causes and recovery:

- With `--story_separator`, epoch count equals the number of non-empty separator-delimited chunks.
- Without a separator, epoch count is derived from `story_start_words` and `story_words_per_epoch`.
- Story mode overrides the ordinary `--epochs` setting. Control cost primarily through `--iterations`, `--save_every`, `--image_width`, and the story chunking options.
