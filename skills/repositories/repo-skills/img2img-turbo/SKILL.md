---
name: img2img-turbo
description: "Route img2img-turbo paired and unpaired image-to-image
  translation, training, dataset validation, and CUDA troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# img2img-turbo

Use this skill for the `GaParmar/img2img-turbo` source checkout. It covers two model families built on Stable Diffusion Turbo:
paired Pix2Pix-Turbo workflows and unpaired CycleGAN-Turbo workflows.

## Start here

1. Read [repository provenance](references/repo-provenance.md) to confirm the skill matches the current checkout.
2. Verify the Python environment with the bundled checker. Pass the source-checkout path with `--repo-root` when you are not already inside the repo root:

   ```bash
   python scripts/check_environment.py --repo-root /path/to/img2img-turbo --scope all --check-help --require-cuda
   ```

   Use `--scope paired`, `--scope unpaired`, or `--scope training` if you only need one route.
3. If you are importing modules directly from the checkout, add `src/` to `PYTHONPATH`; the repository is a source checkout, not a packaged distribution.
4. Route to the focused sub-skill below before writing long commands or code.

## Route by task

- **Paired edge/sketch/custom-checkpoint inference or paired Gradio demos** → [sub-skills/paired-inference/SKILL.md](sub-skills/paired-inference/SKILL.md)
- **Unpaired day/night/rain/clear inference or custom CycleGAN checkpoints** → [sub-skills/unpaired-inference/SKILL.md](sub-skills/unpaired-inference/SKILL.md)
- **Fill50K / horse2zebra training, dataset validation, and checkpoint handoff** → [sub-skills/training/SKILL.md](sub-skills/training/SKILL.md)

## Shared references

- Read [installation and environment](references/installation-and-environment.md) when you need to create or repair a Python/CUDA environment.
- Read [model overview](references/model-overview.md) when choosing between paired and unpaired routes or checking checkpoint expectations.
- Read [troubleshooting](references/troubleshooting.md) for cross-cutting import, CUDA, dependency, and source-checkout failures.
- Read [repository provenance](references/repo-provenance.md) before deciding whether to refresh this skill for a different checkout.

## Shared script

- Run [`scripts/check_environment.py`](scripts/check_environment.py) for a safe no-download smoke check. It can verify source imports, CUDA visibility, and source CLI `--help` checks without launching models or servers.

## Operating notes

- The source scripts construct CUDA-oriented models and do not have a verified CPU fallback for actual image generation or training.
- Keep runtime guidance self-contained. Use the bundled references and scripts instead of pointing future agents back to the original checkout paths.
- Do not assume `pip install .` or `pip install -e .` works here; the repository uses source files under `src/` and the runtime is driven by the checked-out scripts plus the verified Python environment.
- Full checkpoint downloads, long training runs, and Gradio server launches are deliberate actions, not default smoke checks.
