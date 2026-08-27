# Troubleshooting

This file covers the most common issues for the adaptation-and-training sub-skill.

For shared environment, install, credential, and hardware boundaries, also consult the root troubleshooting reference at `../../../references/troubleshooting.md` when it exists in the generated LMOps root.

## Missing raw or domain data

**Symptoms**

- No raw text folder is available.
- A domain corpus exists but the title/context split is inconsistent.
- The selected domain is not one of the supported benchmark families.

**What to do**

- Confirm the input is plain text and not a mixed-format export.
- Make the first line the title when a title exists.
- Keep one document per file for the tiny bundled transformer.
- For full-scale workflows, stage the raw corpus before asking for generated data.

## vLLM or model download problems

**Symptoms**

- The instruction synthesizer cannot load.
- The model is not cached locally.
- GPU memory is insufficient.

**What to do**

- Treat synthesis as a GPU-backed planning concern.
- Verify the model name and cache location before starting.
- Reduce context length or batch size for planning.
- If the model is gated or remote, expect a download or token requirement.

## Huge RedPajama or DCLM inputs

**Symptoms**

- The corpus is too large to stage in one pass.
- Tokenization or scoring takes too long.
- The selected data set never finishes building.

**What to do**

- Split the work into the PDS stages.
- Validate the proxy subset before attempting full scoring.
- Check that the tokenized corpus, proxy subset, and score directory are all distinct.
- Do not conflate baseline pre-training with PDS-selected pre-training.

## Checkpoint paths

**Symptoms**

- A script accepts the path but fails to load weights.
- The wrong checkpoint family is used for the scorer or benchmark.

**What to do**

- Check the family first: domain benchmark, scorer, pretrain model, or ResLoRA base model.
- Confirm the checkpoint root exists and contains the expected files.
- Keep scorer tokenizers aligned with scorer checkpoints.
- Keep benchmark tokenization conventions aligned with the model family.

## Tokenizer mismatch

**Symptoms**

- Selected data decodes incorrectly.
- The scorer sanity check fails.
- Domain benchmark outputs look truncated or shifted.

**What to do**

- Confirm that the scorer tokenizer and data tokenizer match the intended conversion stage.
- For AdaptLLM, confirm whether `add_bos_token` should be on or off.
- For data selection, confirm that the data scorer tokenizer really matches the score-producing model.

## W&B optional logging

**Symptoms**

- Logging is unavailable.
- A run expects a W&B group or name.

**What to do**

- Treat W&B as optional unless the run plan explicitly requires it.
- Disable or omit logging for planning-only checks.
- Never hard-code tokens.

## ResLoRA invalid flags or targets

**Symptoms**

- `merge_flag` is set with no residual mode.
- `pre_num` is missing where residual chaining is required.
- A model family has no matched target modules.
- The target alias list is empty after expansion.

**What to do**

- Run `scripts/reslora_config_check.py` before building a training plan.
- Use one of the supported model families: llama, mistral, roberta, or unet.
- Make sure the target aliases are among the supported family aliases.
- Treat unknown aliases as an error unless you explicitly want a warning-only dry plan.

## Route-out reminders

- If the task is MiniLLM, DPKD, or Tuna, route it to `../distillation-and-post-training/SKILL.md`.
- If the task is VeRL or RL post-training, route it to `../rl-experiential-learning/SKILL.md`.
