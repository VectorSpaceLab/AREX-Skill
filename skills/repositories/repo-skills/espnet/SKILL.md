---
name: espnet
description: "Use when working with ESPnet speech AI toolkit: installation,
  ESPnet2 recipes and training, pretrained inference/model zoo, ESPnet3 stage
  workflows, and repository testing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ESPnet Repo Skill

Use this operating skill when a task involves ESPnet, the end-to-end speech processing toolkit for ASR, TTS, speech translation, enhancement/separation, speaker tasks, diarization, SLU, SVS, SpeechLM, and related audio workflows.

This skill is self-contained. Do not assume the source checkout used to create it is available unless the user is explicitly editing an ESPnet checkout. Prefer the bundled references and scripts here over reopening original docs, examples, or tools.

## First response pattern

1. Classify the request: install/diagnose, prepare recipe data, train/configure, run inference/model-zoo, use ESPnet3 stages, or develop/test ESPnet.
2. Read the matching sub-skill before detailed commands.
3. Use bundled helper scripts when they fit. They are safe by default: no downloads, no package installs, no training, no uploads.
4. Keep backend claims honest. CPU parser/import checks do not prove CUDA, distributed, FlashAttention, k2, or recipe-scale training.

## Minimal package check

```bash
python -c "import espnet2, espnet3; print('ESPnet imports ok')"
```

For source development or editable use, install only the selected task extras, e.g. `pip install -e ".[asr]"` for ASR or `pip install -e ".[tts]"` for TTS. Avoid `.[all]` unless the user truly needs many optional task families.

## Route map

| User intent | Read next | Why |
| --- | --- | --- |
| Install ESPnet, choose extras, diagnose imports or optional tools | [installation-and-diagnostics](sub-skills/installation-and-diagnostics/SKILL.md) | Base dependencies, extras, host tools, CUDA probes, safe environment checker. |
| Create/adapt ESPnet2 recipes, validate `data/`, understand `wav.scp`/`segments`, stage commands, tokenization utilities | [recipes-and-data](sub-skills/recipes-and-data/SKILL.md) | Kaldi-style data layouts, task script stage flow, validation helpers, utility CLIs. |
| Configure/train ESPnet2 models, use `--print_config`, dry-run configs, tune components, resume/fine-tune, GPU/distributed flags | [espnet2-training](sub-skills/espnet2-training/SKILL.md) | Train modules, Task config semantics, dry-run command generation, training troubleshooting. |
| Run pretrained or local inference, use `from_pretrained`, `ModelDownloader`, streaming ASR, enhancement, TTS, packaging | [inference-and-model-zoo](sub-skills/inference-and-model-zoo/SKILL.md) | Inference classes/CLIs, model file pairing, model zoo, packaging checks. |
| Use ESPnet3 System/Hydra stage runner, configs, `--stages`, demo/publication boundaries | [espnet3-workflows](sub-skills/espnet3-workflows/SKILL.md) | ESPnet3 stage order, required config flags, safe stage inspection. |
| Modify ESPnet source, choose tests, debug CI, add recipe/module tests, follow contribution conventions | [development-and-testing](sub-skills/development-and-testing/SKILL.md) | Focused pytest/CI command selection, style, recipe PR policy, maintainer troubleshooting. |

## Shared runtime files

- [references/task-surface.md](references/task-surface.md) maps task families and routing signals.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting failure routing.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot for refresh decisions.
- [scripts/check_import_surface.py](scripts/check_import_surface.py) safely imports selected ESPnet modules.

## Safety boundaries

- Ask before full recipes, dataset acquisition, model downloads, Gradio demos, uploads, long training, or broad CI.
- CUDA is optional unless the user's selected workflow requires GPU runtime.
- Model-zoo tasks are network/cache dependent; validate local file paths before downloads.
