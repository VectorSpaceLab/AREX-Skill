---
name: maestro
description: "Use Maestro for vision-language model fine-tuning, dataset
  validation, model-specific CLI/API workflows, checkpoints, inference, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Maestro repo skill

Use this skill when a task involves Maestro, the Python package for streamlined vision-language model (VLM) fine-tuning with Florence-2, PaliGemma 2, and Qwen2.5-VL.

## Read first

- [Repository provenance](references/repo-provenance.md): read before deciding whether this skill matches a current checkout or package version.
- [Installation and CLI](references/installation-and-cli.md): install commands, package extras, CLI command map, and environment variables.
- [Root troubleshooting](references/troubleshooting.md): package-wide import, optional dependency, backend, CLI warning, and training-output issues.
- [check_maestro_environment.py](scripts/check_maestro_environment.py): safe installed-package import/version/backend probe.
- [maestro_cli_probe.py](scripts/maestro_cli_probe.py): safe CLI route probe that does not train or download models.

## Choose a route

| User task | Open |
| --- | --- |
| Validate JSONL/COCO data, parse Roboflow identifiers, create DataLoaders, select metrics, or handle device/reproducibility helpers | [datasets-and-metrics](sub-skills/datasets-and-metrics/SKILL.md) |
| Build Florence-2 train commands/API calls, load or save Florence checkpoints, run Florence inference, or format Florence `<OD>` detections | [florence-2](sub-skills/florence-2/SKILL.md) |
| Fine-tune or infer with PaliGemma 2 for JSON extraction, VQA, OCR-style prompts, LoRA/QLoRA/freeze choices, or PaliGemma checkpoints | [paligemma-2](sub-skills/paligemma-2/SKILL.md) |
| Fine-tune or infer with Qwen2.5-VL, build Qwen chat conversations, control pixel bounds, or format Qwen COCO detection JSON | [qwen-2-5-vl](sub-skills/qwen-2-5-vl/SKILL.md) |

## Install decision points

Maestro's model extras can pull different optional dependencies. Prefer one environment per model family for real training, especially when mixing QLoRA, `bitsandbytes`, `flash-attn`, or experimental Qwen support.

```bash
pip install maestro
pip install "maestro[florence_2]"
pip install "maestro[paligemma_2]"
pip install "maestro[qwen_2_5_vl]"
```

For safe package inspection, import checks, dataset validation, formatter checks, and CLI help do not require model downloads. Full fine-tuning and inference may require Hugging Face model access, Roboflow credentials, GPU memory, and large downloads.

## Minimal import and CLI checks

```bash
python - <<'PY'
from importlib.metadata import version
import maestro
print(version("maestro"))
PY

maestro --help
maestro version
maestro info
```

Or use bundled diagnostics from this skill tree:

```bash
python scripts/check_maestro_environment.py --models all --json
python scripts/maestro_cli_probe.py --include-model-help --json
```

## Common cross-skill rules

- Validate dataset shape before building a training command. Maestro's common loader expects `train`, `valid`, and `test` splits for training.
- Use local dataset paths for reproducible runs. Roboflow identifiers require `ROBOFLOW_API_KEY` and may download data.
- Use `device="auto"` unless the user has a specific visible backend requirement.
- Use model-specific formatter callbacks for COCO object-detection datasets. Florence-2 and Qwen2.5-VL expose formatter helpers; PaliGemma 2 in this Maestro version does not expose a dedicated detection formatter API.
- CLI options use underscores in this repo (`--batch_size`, `--optimization_strategy`, `--max_new_tokens`). Some bundled config helpers use hyphenated helper flags but emit Maestro-compatible underscore CLI flags.
- Do not treat safe import/formatter checks as proof that a full GPU fine-tuning run, model download, or Roboflow download will succeed.
