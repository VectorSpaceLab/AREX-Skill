---
name: autotrain-advanced
description: "Routes AutoTrain Advanced installation, CLI, config, training,
  UI/API, backend, and utility workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AutoTrain Advanced

Use this skill for the Hugging Face AutoTrain Advanced repository: the top-level `autotrain` CLI, config-driven training, the FastAPI UI/API, backend runners, and bundled model utilities.

Start here for install, command discovery, and route selection. Then jump to the focused sub-skill that matches the task family.

## Install and inspect

- Install the package in editable mode from the repo root:
  `python -m pip install -e .`
- Install a compatible PyTorch stack for your platform before GPU-backed workflows.
  The repo expects `torch`, `torchvision`, and `torchaudio` to be available.
- Minimal import check:
  `python -c "import autotrain; print(autotrain.__version__)"`
- Use `scripts/check_install.py` when you want a quick import/version check.
- Use `scripts/inspect_cli.py --help` to inspect the CLI without opening source files.
- Use `scripts/check_backends.py` when you need to see the current torch/CUDA view.

## Route map

Read `references/workflow-map.md` for the command-family map, supported task families, and the one important exception: `vlm` is supported through the app/API/config paths, not as a top-level `autotrain vlm` command.

- `sub-skills/cli-config/` — install, `autotrain --help`, `--version`, `--config`, `setup`, parser behavior, and config validation.
- `sub-skills/llm-training/` — `autotrain llm`, LLM finetuning configs, quantization, PEFT, unsloth, and adapter workflows.
- `sub-skills/text-and-tabular/` — text classification/regression, token classification, seq2seq, extractive QA, sentence-transformers, and tabular training.
- `sub-skills/vision-multimodal/` — image classification/regression, object detection, and VLM workflows through the app/API/config path.
- `sub-skills/app-backends/` — `autotrain app`, `autotrain api`, `autotrain spacerunner`, local/cloud backends, auth, jobs, and logs.
- `sub-skills/model-tools/` — `autotrain tools merge-llm-adapter` and `autotrain tools convert_to_kohya`.

## When to read deeper

- Read `references/troubleshooting.md` for install, import, backend, auth, and data-layout failures that affect more than one route.
- Read `references/repo-provenance.md` when you need to confirm whether this skill still matches the current repository checkout or when refreshing it later.
- Read the owning sub-skill before giving concrete commands, config fields, dataset checks, or backend-specific recovery steps.

## Good first checks

- `autotrain --help`
- `autotrain <subcommand> --help`
- `python -m pip check`
- `python -c "import autotrain; print(autotrain.__version__)"`

## Notes

- The repository is multi-modal and config-driven; route by task family, not only by source folder.
- The UI/API has broader task coverage than the top-level CLI for some workflows, especially VLM.
- Keep runtime links inside this generated skill tree; do not point future agents back at the source checkout.
