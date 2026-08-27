# Local Inference Workflows

These workflows mirror the repo's local CLI and demo-shell recipes, but they stay self-contained and safe to reason about. Use the bundled dry-run helper first whenever you need a command checked before generation.

## 1) Render first, run later

Use the safe helper to validate a recipe without importing the model stack or starting GPU work.

```bash
python scripts/local_inference_cli_dry_run.py \
  --profile instruct \
  --model-id ./HunyuanImage-3-Instruct \
  --prompt "A polished product poster for a travel app" \
  --image ./reference_1.png,./reference_2.png \
  --save ./outputs/poster.png
```

What the helper should do:

- render the equivalent bundled-runner command;
- warn about missing checkpoint paths, missing image files, missing credentials, or requested optional accelerators;
- refuse clearly invalid combinations before any generation command is launched.

## 2) Base text-to-image

Use the base checkpoint when you only need text-to-image generation.

```bash
python scripts/run_hunyuan_image_generation.py \
  --model-id ./HunyuanImage-3 \
  --prompt "A brown and white dog running on grass" \
  --bot-task image \
  --image-size 1024x1024 \
  --save ./outputs/image.png \
  --seed 41 \
  --reproduce \
  --attn-impl sdpa \
  --moe-impl eager
```

Optional speed-up branch, only when the accelerator is installed and ready:

- change `--moe-impl eager` to `--moe-impl flashinfer`.

## 3) Instruct / TI2I

Use the instruct checkpoint for editing, multi-image fusion, and reasoning-style recaption flows.

```bash
python scripts/run_hunyuan_image_generation.py \
  --model-id ./HunyuanImage-3-Instruct \
  --prompt "Create a cleaner poster from the reference images" \
  --image ./reference_1.png,./reference_2.png \
  --bot-task think_recaption \
  --use-system-prompt en_unified \
  --image-size auto \
  --infer-align-image-size \
  --save ./outputs/edit.png \
  --seed 43 \
  --reproduce \
  --attn-impl sdpa \
  --moe-impl eager
```

Multi-image TI2I uses the same command shape, with one, two, or three comma-separated images. The repo demos show all three patterns.

## 4) Distilled instruct

Use the distil checkpoint when you want the same instruct behavior with fewer sampling steps.

```bash
python scripts/run_hunyuan_image_generation.py \
  --model-id ./HunyuanImage-3-Instruct-Distil \
  --prompt "Create a cleaner poster from the reference images" \
  --image ./reference_1.png,./reference_2.png,./reference_3.png \
  --bot-task think_recaption \
  --use-system-prompt en_unified \
  --image-size auto \
  --infer-align-image-size \
  --diff-infer-steps 8 \
  --save ./outputs/edit_distil.png \
  --seed 44 \
  --reproduce \
  --attn-impl sdpa \
  --moe-impl eager
```

## 5) Reproduction and determinism

When reproducibility matters:

- set `--seed` explicitly;
- add `--reproduce`;
- keep the checkpoint, prompt, image list, and `--image-size` fixed;
- avoid changing `--diff-infer-steps`, `--bot-task`, or Taylor Cache settings between runs.

The code path also sets deterministic CUDA behavior, so reproduction is only meaningful on a compatible GPU stack.

## 6) Taylor Cache tuning

Add Taylor Cache only when you understand the sampling tradeoff.

```bash
python scripts/run_hunyuan_image_generation.py \
  --model-id ./HunyuanImage-3-Instruct \
  --prompt "..." \
  --image ./reference_1.png \
  --bot-task think_recaption \
  --use-system-prompt en_unified \
  --use-taylor-cache \
  --taylor-cache-interval 5 \
  --taylor-cache-order 2 \
  --taylor-cache-enable-first-enhance \
  --taylor-cache-first-enhance-steps 3 \
  --taylor-cache-enable-tailing-enhance \
  --taylor-cache-tailing-enhance-steps 1 \
  --taylor-cache-low-freqs-order 2 \
  --taylor-cache-high-freqs-order 2
```

## 7) Rewrite-oriented branch

When you want the CLI to rewrite the prompt before generation:

- set `--rewrite`;
- provide Tencent Cloud credentials in the environment;
- run the dry-run helper first so it can catch missing credentials or malformed combinations;
- treat the current branch as experimental because the source snapshot has a parser mismatch in this path.

## 8) Demo-shell recipes as references

The repository's `run_demo_instruct.sh` and `run_demo_instruct_distil.sh` are best treated as frozen example sets:

- they hard-code checkpoint assumptions;
- they assume expensive GPU generation;
- they use `--moe-impl flashinfer` in the upstream examples, and the distil recipe also uses `--diff-infer-steps 8`.
- they are useful as flag templates, not as a script to source inside automation.

Translate them into explicit bundled-runner commands or let the dry-run helper render them.
