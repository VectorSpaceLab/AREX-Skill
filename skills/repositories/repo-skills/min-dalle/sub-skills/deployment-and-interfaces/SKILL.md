---
name: deployment-and-interfaces
description: "Routes min(DALL·E) command-line, notebook, Tkinter GUI, and
  Replicate/Cog interface workflows beyond direct MinDalle API calls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# deployment-and-interfaces

Use this sub-skill when the task is about min(DALL·E) public interfaces outside a direct `MinDalle` API call: command-line usage, Colab/notebook patterns, the Tkinter UI, Replicate/Cog deployment, predictor filenames, output paths, or interface-specific troubleshooting.

## Start here

- Read [references/cli-reference.md](references/cli-reference.md) for the original `image_from_text.py` flags, defaults, save behavior, ASCII preview, and the verified absence of an installed console command.
- Read [references/interface-workflows.md](references/interface-workflows.md) for the Colab/notebook flow, Tkinter controls and limits, Replicate predictor inputs/defaults/ranges, filename sanitation, output extensions, Cog pins, and deployment caveats.
- Read [references/troubleshooting.md](references/troubleshooting.md) when the user reports a missing command, slow downloads/inference, CPU/FP16 problems, display errors, Cog/CUDA issues, unexpected Replicate filenames, or progressive-output counts.

## Bundled helpers

- [scripts/min_dalle_cli_template.py](scripts/min_dalle_cli_template.py) is the safe replacement for the original command-line script. It defaults to `--dry-run`; add `--run` only when the user explicitly wants model construction, possible downloads, and inference.
- [scripts/replicate_filename_sanitize.py](scripts/replicate_filename_sanitize.py) previews the Replicate-style output basename without requiring Cog or model loading.

Useful no-network checks:

```bash
python scripts/min_dalle_cli_template.py --help
python scripts/min_dalle_cli_template.py --text "artificial intelligence" --no-mega --top-k 256
python scripts/replicate_filename_sanitize.py --self-test
python scripts/replicate_filename_sanitize.py --text "Dali painting of WALL·E"
```

## Boundary routes

- For direct `MinDalle` construction, `generate_image`, `generate_image_stream`, sampling arguments, tensor/PIL image semantics, and reusable model lifetime, route to [../text-to-image-generation/SKILL.md](../text-to-image-generation/SKILL.md).
- For model weight downloads, `models_root`, cache layout, device selection, dtype/backend behavior, CUDA/CPU trade-offs, and environment setup, route to [../model-assets-and-runtime/SKILL.md](../model-assets-and-runtime/SKILL.md).
- Do not tell future agents to run the original repository scripts or notebook. Use this sub-skill's bundled helpers and distilled references instead.
