---
name: edge-connect
description: "Route EdgeConnect requests for image inpainting setup, data
  preparation, training, checkpoint-backed testing, and evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# EdgeConnect

EdgeConnect is a generative image inpainting repository built around adversarial edge learning. The practical workflow is:
1. prepare images, masks, edges, and file lists,
2. choose a training stage and checkpoints,
3. run checkpoint-backed test-time inference,
4. score the generated outputs.

Use this skill whenever the request names EdgeConnect or refers to the repo's `train.py`, `test.py`, `config.yml.example`, `EdgeModel_gen.pth`, `InpaintingModel_gen.pth`, `samples/`, `results/`, `flist` files, masked images, edge maps, or PSNR/SSIM/MAE/FID evaluation on EdgeConnect outputs.

## Read first

- `references/repo-provenance.md` if you need to know whether this skill matches the current checkout.
- `references/installation.md` for the legacy-compatible environment and the recommended smoke check.
- `references/troubleshooting.md` for cross-cutting environment, YAML, and checkpoint issues.

## Router map

- `sub-skills/data-preparation/` — image, mask, and edge layouts; flists; config path validation.
- `sub-skills/training/` — stage selection, checkpoint resume, losses, sampling, and internal validation.
- `sub-skills/testing/` — checkpoint-backed inference, command construction, and checkpoint layout checks.
- `sub-skills/evaluation/` — PSNR/SSIM/MAE/FID scoring and input validation after outputs exist.

## How to choose

- Pick `data-preparation` when the user is asking how to lay out images, masks, or edge maps, or how to build and validate file lists.
- Pick `training` when the user wants to start, resume, or explain a training run, stage, loss, or checkpoint bundle.
- Pick `testing` when the user wants to run `test.py`, validate checkpoint contents, or construct an inference command.
- Pick `evaluation` when the user already has generated outputs and wants pixel metrics or FID input checks.

## Environment notes

- This repo is legacy. Use a compatibility set that keeps `scipy.misc.imread`, `scipy.misc.imresize`, and `yaml.load(...)` working.
- A known-working baseline is Python 3.7 with CUDA-enabled Torch plus the legacy scientific stack listed in `references/installation.md`.
- A modern PyYAML 6.x install breaks `src.config.Config`; use a compatible PyYAML version or patch the loader call.
- Do not rely on `train.py --help` or `test.py --help` as side-effect-free smoke checks; use `scripts/check_env.py` instead.

## Minimal smoke check

Run the bundled environment checker from a neutral working directory:

```bash
python scripts/check_env.py --repo-root <EdgeConnect checkout> --cuda
```

If you only need CPU importability, omit `--cuda`. The checker imports the repo modules, instantiates the example config, and performs an optional tiny CUDA allocation when requested.

## Key terms

- `MODE` selects train, test, or eval.
- `MODEL` selects edge, inpaint, edge-inpaint, or joint behavior.
- `MASK=6` is the test-only one-to-one mask mode.
- `EDGE=2` means external edge maps are required.
- The checkpoint directory is both the config home and the weight home.

## Common launch patterns

- Data prep: build flists, validate config paths, and confirm paired image/mask/edge ordering.
- Training: generate `config.yml`, confirm the stage and GPU list, then launch the right model family.
- Testing: validate the checkpoint directory first, then run stage-appropriate inference.
- Evaluation: confirm prediction/ground-truth pairings before scoring.

## When to read the subskill references

- Read a subskill's references if you need exact command shape, config fields, data layout rules, or failure recovery steps.
- Read `references/installation.md` before creating an environment or changing dependency versions.
- Read `references/troubleshooting.md` when import or runtime behavior looks inconsistent with the expected legacy stack.
