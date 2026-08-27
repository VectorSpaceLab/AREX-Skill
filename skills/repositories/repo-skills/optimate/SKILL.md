---
name: optimate
description: "Routes OptiMate workflows for Speedster inference optimization,
  NebullVM backend selection, Forward-Forward training, OpenAlphaTensor
  training, and ChatLLaMA RLHF setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# OptiMate

Use this skill for the repository's public workflows around model optimization, backend selection, standalone training engines, and ChatLLaMA RLHF setup.

## Route map

| If the user asks about... | Start here |
| --- | --- |
| `speedster`, `optimize_model`, `save_model`, `load_model`, compiler/backend filtering, latency summaries, or model acceleration | `sub-skills/speedster-optimization/SKILL.md` |
| `nebullvm`, `DataManager`, `check_device`, compiler selection, optional backend probing, or device parsing | `sub-skills/nebullvm-backends/SKILL.md` |
| Forward-Forward training, MNIST or Aesop Fables loaders, progressive/recurrent/NLP model types, or Python 3.9 compatibility | `sub-skills/forward-forward-training/SKILL.md` |
| OpenAlphaTensor configs, checkpoints, matrix-multiplication search, or the `main.py` training CLI | `sub-skills/open-alpha-tensor/SKILL.md` |
| ChatLLaMA datasets, config YAMLs, actor/reward/RLHF training, DeepSpeed, or PEFT setup | `sub-skills/chatllama-rlhf/SKILL.md` |

## Read first

- `references/repo-provenance.md`
- `references/package-map.md`
- `references/installation-and-backends.md`
- `references/troubleshooting.md`
- `references/repo-routing-metadata.json`

## Shared behavior

- Treat the source checkout as evidence only; the skill tree must stand on its own.
- Use the nearest sub-skill for concrete API, CLI, data, or workflow detail.
- If a request spans packages, start with the most specific sub-skill and then read the root references for shared backend or environment guidance.
- Keep training and optimization detail out of the root router; do not duplicate long API tables here.

## Minimal smoke probe

Use the bundled helper to verify that the public package roots import and the host backend is visible:

```bash
python scripts/check_optimate_environment.py --modules speedster,nebullvm --check-cuda
```

For Forward-Forward and ChatLLaMA compatibility questions, prefer the sub-skill scripts because they encode the source-era Python and dependency constraints.
