# `imagine` CLI reference

This reference is self-contained for the `deep-daze` 0.11.1 command-line entry point:

```text
imagine = deep_daze.cli:main
```

The command is implemented with Python Fire around a `train(...)` function. Invoking `imagine` starts generation; it may also initialize CLIP and download model weights. Use `scripts/build_imagine_command.py` when you only need to print or validate a command.

## Command shape

```bash
imagine [TEXT] --flag=value --other_flag=value
```

- `TEXT` is the positional text prompt and maps to the CLI `text` argument.
- Image-only optimization omits `TEXT` and passes `--img=PATH`.
- Text+image optimization supplies both `TEXT` and `--img=PATH`; their CLIP encodings are averaged.
- Start-image priming is separate from image-target conditioning: `--start_image_path=PATH` first trains the generator toward that image, then the normal text/image objective takes over.
- The CLI signature uses snake_case flag names. Some Fire examples use hyphenated names, but snake_case is the safest spelling when recovering commands.
- Boolean values should be passed explicitly in automation, for example `--open_folder=False`, `--save_progress=True`, and `--create_story=True`.

## Verified package and model facts

- Installed distribution observed for this skill: `deep-daze` 0.11.1.
- Import surface exports `DeepDaze` and `Imagine`.
- Console script: `imagine`.
- Available CLIP model names: `RN50`, `RN101`, `RN50x4`, `ViT-B/32`, `ViT-L/14`.
- Default `model_name`: `ViT-B/32`.
- Default optimizer: `AdamP`.
- CLIP text tokenization uses a context length of 77; a short prompt such as `a house` tokenizes to shape `(1, 77)`.

## Positional argument and flags

Defaults below come from the CLI function signature used by the console script.

| CLI argument | Default | Use |
| --- | ---: | --- |
| `TEXT` / `text` | `None` | Prompt to visualize. In normal mode, keep it within CLIP's 77-token context. |
| `--img` | `None` | Path to a JPG/PNG image to optimize toward. May be used alone or with `TEXT`. |
| `--learning_rate` | `1e-5` | Main SIREN optimization learning rate. |
| `--num_layers` | `16` | Hidden layers in the SIREN generator. More layers can improve detail but cost memory/time. |
| `--hidden_size` | `256` | Width of SIREN hidden layers. Larger values cost memory/time. |
| `--batch_size` | `4` | Number of generated cutouts/images evaluated per loss batch. Lower for memory pressure. |
| `--gradient_accumulate_every` | `4` | Accumulates multiple batches before optimizer step. Increase when lowering batch size. |
| `--epochs` | `20` | Outer training epochs. Story mode may override this from the story length. |
| `--iterations` | `1050` | Optimization iterations per epoch. This is the main runtime multiplier. |
| `--save_every` | `100` | Save a progress frame when `iteration % save_every == 0` and progress saving is enabled. |
| `--image_width` | `512` | Square output resolution. Lowering to `256` is the primary low-memory knob. |
| `--deeper` | `False` | If true, overrides `num_layers` to `32`. |
| `--overwrite` | `False` | If false and the target final image already exists, the CLI asks before overwriting. |
| `--save_progress` | `True` | Saves intermediate frames and the latest non-sequence image during training. |
| `--seed` | `None` | Sets torch/random seeds for deterministic attempts. |
| `--open_folder` | `True` | Attempts to open the current output folder through the OS. Disable on headless systems. |
| `--save_date_time` | `False` | Prepends a timestamp to generated filenames, reducing collision risk. |
| `--start_image_path` | `None` | Path to an image used to prime the generator before normal optimization. |
| `--start_image_train_iters` | `50` | Number of priming iterations for `start_image_path`. |
| `--theta_initial` | `None` | Optional first-layer frequency hyperparameter; underlying default is `30`. |
| `--theta_hidden` | `None` | Optional hidden-layer frequency hyperparameter; underlying default is `30`. |
| `--start_image_lr` | `3e-4` | Learning rate for start-image priming. |
| `--lower_bound_cutout` | `0.1` | Lower random-cutout size fraction. Keep below `0.8`. |
| `--upper_bound_cutout` | `1.0` | Upper random-cutout size fraction. Usually leave at `1.0`. |
| `--saturate_bound` | `False` | Increases lower cutout bound toward `0.75` during training. |
| `--create_story` | `False` | Uses changing prompt windows across epochs for long prose. Requires text input. |
| `--story_start_words` | `5` | Initial word-window size for story mode. |
| `--story_words_per_epoch` | `5` | New words added per story epoch when no separator is used. |
| `--story_separator` | `None` | Separator such as `.` for chunking story epochs. Ignored if absent from text. |
| `--averaging_weight` | `0.3` | Weight for averaged cutout features versus individual cutout features. |
| `--gauss_sampling` | `False` | Uses Gaussian cutout size sampling instead of uniform sampling. |
| `--gauss_mean` | `0.6` | Mean for Gaussian cutout sampling. |
| `--gauss_std` | `0.2` | Standard deviation for Gaussian cutout sampling. |
| `--do_cutout` | `True` | Enables random cutout augmentation. Leave enabled unless intentionally experimenting. |
| `--center_bias` | `False` | Samples cutout locations near image center. |
| `--center_focus` | `2` | Strength of center bias when enabled. |
| `--jit` | `True` | Requests JIT CLIP loading. The runtime disables it automatically when torch is not 1.7.1. |
| `--save_gif` | `False` | After training, writes a GIF from progress frames if `save_progress` is true. |
| `--save_video` | `False` | After training, writes an MP4 from progress frames if `save_progress` is true and the writer is available. |
| `--model_name` | `ViT-B/32` | CLIP model name or a local checkpoint path. Prefer known model names in portable commands. |
| `--optimizer` | `AdamP` | Optimizer name. Supported values in the implementation are `AdamP`, `Adam`, and `DiffGrad`. |

## Output artifacts and filenames

The CLI writes outputs in the process working directory. Run `imagine` from the directory where generated artifacts should be created.

- The base output name comes from the prompt with spaces replaced by underscores, truncated to CLIP context length. For image-only optimization, it comes from the image filename stem.
- Final/current image: `<base>.jpg`.
- Progress frames after the first save: `<base>.<sequence>.jpg`, where `sequence` is zero-padded to six digits and advances according to `epoch * iterations + iteration`, divided by `save_every`. The initial sequence value is `0`; because it is falsey in the implementation, that first save updates `<base>.jpg` rather than writing `<base>.000000.jpg`.
- With `--save_date_time=True`, a timestamp prefix is added to each generated filename.
- Story mode also writes `story_transitions.txt` in the working directory, recording epoch/sequence/prompt-window transitions.
- `--save_gif=True` writes `<base>.gif` after training, but only when progress frames were saved.
- `--save_video=True` writes `<base>.mp4` after training, but only when progress frames were saved and an MP4 writer is available.
- `--open_folder=True` tries to open the working directory once at startup; set `False` for servers, notebooks, CI, SSH sessions, and other headless environments.

## Practical resource presets

These are command-construction presets, not package defaults. They are meant to keep first runs bounded.

| Preset | Suggested flags | Use |
| --- | --- | --- |
| Smoke | `--epochs=1 --iterations=10 --save_every=5 --image_width=256 --num_layers=8 --hidden_size=128 --batch_size=1 --gradient_accumulate_every=4` | Fast command validation or runtime smoke test. |
| Low VRAM | `--epochs=1 --iterations=50 --save_every=10 --image_width=256 --num_layers=16 --batch_size=1 --gradient_accumulate_every=16` | Small GPU memory, CPU fallback, or exploratory prompt checks. |
| Balanced | `--epochs=4 --iterations=100 --save_every=25 --image_width=512 --num_layers=24 --batch_size=4 --gradient_accumulate_every=4` | Medium-quality run after setup is proven. |
| Quality | `--epochs=10 --iterations=300 --save_every=50 --image_width=512 --num_layers=32 --batch_size=8 --gradient_accumulate_every=2` | More expensive run; confirm GPU/model availability first. |

For full default-generation behavior, omit the preset flags and accept the CLI defaults. Do that only after runtime constraints are understood.

## CLI-only exclusions

The command-line wrapper does not expose every Python constructor argument. In particular, custom `clip_encoding` workflows and direct method calls are Python API work; route those to [../../python-api/SKILL.md](../../python-api/SKILL.md).
