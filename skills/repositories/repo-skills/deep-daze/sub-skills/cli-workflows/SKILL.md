---
name: cli-workflows
description: "Use the deep-daze imagine CLI for text, image, story, priming,
  progress, and output workflow command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLI workflows

Use this sub-skill when the task is to construct, adapt, or recover a `deep-daze` `imagine` command-line workflow. It covers text prompts, image-target conditioning, text+image conditioning, start-image priming, story mode, progress/GIF/video outputs, output naming, overwrite prompts, and headless-safe command construction.

For long flag tables and defaults, read [references/cli-reference.md](references/cli-reference.md). For practical commands, read [references/workflow-recipes.md](references/workflow-recipes.md). For failures, read [references/troubleshooting.md](references/troubleshooting.md). To build a command without running generation, use [scripts/build_imagine_command.py](scripts/build_imagine_command.py).

## Routing boundaries

- Use this sub-skill for the console entry point `imagine` and the CLI function arguments exposed by that command.
- Route Python-only `DeepDaze` / `Imagine` class usage, custom encodings, and method-level adaptation to [../python-api/SKILL.md](../python-api/SKILL.md).
- Route CLIP model cache, model download, device, backend, dependency, and hardware setup issues to [../runtime-and-models/SKILL.md](../runtime-and-models/SKILL.md).

## Operating defaults

- Prefer short, explicit, reproducible commands before expensive generation: set small `epochs`, `iterations`, `image_width`, `batch_size`, and `save_every` until the prompt and output behavior are confirmed.
- On headless or automated systems, set `--open_folder=False` so the CLI does not try to launch a desktop file browser.
- To avoid blocking on an overwrite prompt, either use `--save_date_time=True` for unique names or intentionally set `--overwrite=True` only when replacing the existing output is acceptable.
- Keep prompts under CLIP's 77-token context in normal mode. For longer prose, use `--create_story=True` with `--save_progress=True` and optionally a `--story_separator`.

## Command-builder quick start

From this sub-skill directory, print a safe smoke-test command without starting generation:

```bash
python scripts/build_imagine_command.py --prompt "a small house in a misty forest"
```

For a low-memory command using an image target and start-image priming:

```bash
python scripts/build_imagine_command.py \
  --prompt "a watercolor night sky" \
  --img inputs/target.jpg \
  --start-image inputs/prime.jpg \
  --preset low-vram
```

Copy the printed `imagine ...` command, run it from the directory where output artifacts should be written, and keep expensive runs bounded until the runtime/model setup is known to be ready.
