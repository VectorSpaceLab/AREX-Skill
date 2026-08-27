---
name: prompt-optimization
description: "Operate ProTeGi text prompt optimization and Promptist
  text-to-image prompt rewriting workflows for LMOps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Prompt Optimization

Use this operating sub-skill when the user asks for LMOps prompt optimization, prompt rewriting, or prompt-optimization run planning.

## Route by task shape

- **ProTeGi text prompt optimization**: use for automatic optimization of zero-shot binary classification prompts with labeled train/test data, markdown seed prompts, and an approved chat/completion provider budget.
- **Promptist prompt rewriting**: use for text-to-image prompt rewriting with the pretrained Promptist prompter model, but plan offline first to avoid accidental model downloads.
- **Promptist RL training**: use only for planning or explicitly approved heavy execution; it needs training prompt data, a supervised prompter checkpoint, Stable Diffusion/CLIP/aesthetic reward assets, Accelerate/TRL, GPUs, and credentials.
- **Retrieval-based prompt or demonstration selection**: route to `../example-retrieval/SKILL.md`.
- **Domain/instruction corpus conversion or model adaptation before prompt work**: route to `../adaptation-and-training/SKILL.md`.
- **Broad LMOps project routing**: consult `../../references/project-index.md` if the user names a different LMOps project.

## Required first checks

1. Classify the request as ProTeGi optimization, Promptist pretrained rewrite planning, Promptist RL training planning, or a route-out case.
2. Confirm required inputs before any expensive or external action:
   - ProTeGi: task name, task data directory, seed prompt markdown file(s), output log path, evaluator, scorer, provider credentials, overwrite consent, and budget/concurrency limits.
   - Promptist rewrite: plain text prompt(s), model id, tokenizer id, model cache or network consent, and CPU/GPU expectation for any real model load.
   - Promptist RL training: data directory, supervised prompter checkpoint, Stable Diffusion model access, TRL/PPO config, checkpoint directory, distributed launch plan, GPU availability, Hugging Face access, and W&B/logging policy.
3. Use the bundled safe planners before any source checkout run:
   - `python scripts/protegi_command_builder.py --help`
   - `python scripts/promptist_rewrite_skeleton.py --help`
4. Read the focused runtime references:
   - `references/protegi-cli-and-api.md`
   - `references/promptist-workflows.md`
   - `references/troubleshooting.md`

## Safe operating defaults

- Do not run model downloads, provider calls, image generation, PPO training, Docker/container startup, or multi-node launches unless the user explicitly asks and provides the needed environment and credentials.
- Treat bundled scripts as planners and validators. They do not import LMOps source code, call model providers, load Promptist models, download weights, generate images, or train.
- Promptist GPU/model-download workflows and multi-node RL training are documented but not creation-time verified by this sub-skill.
- Treat ProTeGi output files as user data: the native program removes an existing output file before writing, so ask before overwriting.

## Quick ProTeGi planning pattern

1. Choose one of the supported native task names: `ethos`, `jailbreak`, `liar`, or `ar_sarcasm`.
2. Stage task data in the required layout and one or more seed prompt markdown files with a `# Task` section and `{{ text }}` placeholder.
3. Build a command without executing it:

```bash
python scripts/protegi_command_builder.py \
  --task liar \
  --data-dir data/my_binary_task \
  --prompts prompts/seed.md \
  --out runs/my_binary_task.ucb.out \
  --evaluator ucb \
  --scorer 01 \
  --path-policy warn
```

4. Resolve any warnings, confirm credentials and overwrite behavior, then run the emitted command only in a prepared ProTeGi environment.

## Quick Promptist planning pattern

1. Start with the offline skeleton and keep model loading off:

```bash
python scripts/promptist_rewrite_skeleton.py \
  --plain-text "A rabbit is wearing a space suit" \
  --model-id microsoft/Promptist \
  --tokenizer-id gpt2 \
  --show-prompts
```

2. If the user approves a real rewrite run, confirm PyTorch/Transformers availability and whether the Promptist model and tokenizer are already cached or may be downloaded.
3. If the user asks for RL training, move to the training checklist in `references/promptist-workflows.md` and do not treat it as a small smoke test.
