---
name: deep-daze
description: "Use deep-daze for CLIP-guided Siren image generation through the
  imagine CLI and Python APIs, with runtime inspection and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deep Daze

Use this repo skill when a task involves the `deep-daze` / `deep_daze` package:
CLIP-guided text-to-image generation, image-conditioned generation, start-image
priming, story mode, the `imagine` command, or programmatic `Imagine` and
`DeepDaze` usage.

Deep Daze combines OpenAI CLIP guidance with a Siren generator. Generation is an
optimization run, not a one-shot inference call: it can download CLIP weights,
consume substantial VRAM or CPU time, and write image/progress artifacts in the
current working directory.

## Quick install and identity checks

Install the public package in the user's environment:

```bash
python -m pip install deep-daze
```

Minimal import and package-data check:

```bash
python - <<'PY'
from deep_daze import DeepDaze, Imagine
from deep_daze.clip import available_models, tokenize
print(DeepDaze.__name__, Imagine.__name__)
print(available_models())
print(tuple(tokenize('a house').shape))
PY
```

Expected CLIP model names are `RN50`, `RN101`, `RN50x4`, `ViT-B/32`, and
`ViT-L/14`; `ViT-B/32` is the default model. `tokenize('a house')` should return
shape `(1, 77)`.

For a safe inspection that does not download model checkpoints or generate
images, run the bundled helper:

```bash
python scripts/deep_daze_inspect.py
```

Read [references/usage-overview.md](references/usage-overview.md) for the
package concept map and [references/troubleshooting.md](references/troubleshooting.md)
for cross-cutting failures.

## Route by task

| User task | Read next |
|---|---|
| Verify install/import, dependency presence, CLIP model names, tokenizer package data, cache/download behavior, CPU/GPU backend status, or VRAM expectations. | [sub-skills/runtime-and-models/SKILL.md](sub-skills/runtime-and-models/SKILL.md) |
| Build or debug an `imagine` command for text prompts, image targets, text+image conditioning, start-image priming, story mode, progress frames, GIF/video output, or headless execution. | [sub-skills/cli-workflows/SKILL.md](sub-skills/cli-workflows/SKILL.md) |
| Use `deep_daze.Imagine` or lower-level `DeepDaze` from Python, translate CLI settings into code, inspect signatures/defaults, use custom CLIP encodings, or control output paths programmatically. | [sub-skills/python-api/SKILL.md](sub-skills/python-api/SKILL.md) |

## Safe operating defaults

- Start with small `epochs`, `iterations`, `image_width`, and `batch_size` until
  the prompt, output path, and runtime are known to work.
- Use `open_folder=False` in scripts, notebooks, remote shells, and headless
  agents.
- Use `save_date_time=True` or a clean output directory to avoid CLI overwrite
  prompts.
- Keep ordinary prompts within CLIP's 77-token context. Use story mode for long
  prose, with `save_progress=True` when the transition frames matter.
- Treat full generation as a potentially long/networked run. It may download a
  CLIP checkpoint into the user's cache before training starts.

## Useful entry points

- CLI: `imagine "a house in the forest" --open_folder=False`
- Python: `from deep_daze import Imagine`
- Runtime CLIP utilities: `from deep_daze.clip import available_models, tokenize`
- Lower-level generator module: `from deep_daze import DeepDaze`

## Validation guidance

Use the bundled inspection helpers and CLI/API probes before expensive runs:

- [scripts/deep_daze_inspect.py](scripts/deep_daze_inspect.py) checks the shared
  package/runtime surface.
- [sub-skills/runtime-and-models/scripts/check_deep_daze_runtime.py](sub-skills/runtime-and-models/scripts/check_deep_daze_runtime.py)
  performs a deeper runtime preflight.
- [sub-skills/cli-workflows/scripts/build_imagine_command.py](sub-skills/cli-workflows/scripts/build_imagine_command.py)
  builds a shell-quoted command without running generation.
- [sub-skills/python-api/scripts/probe_api_surface.py](sub-skills/python-api/scripts/probe_api_surface.py)
  checks API signatures/defaults without constructing `Imagine`.

## Provenance and refresh

Read [references/repo-provenance.md](references/repo-provenance.md) before using
this skill against a different checkout or package version. If the source
commit, dirty state, package version, public entry points, CLI signature, or
core source layout changed, refresh the repo skill before relying on details.
