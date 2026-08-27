# PaLM Pretraining Workflows

## Purpose

This reference distills the repository's PaLM pretraining recipe into a self-contained summary. It is intentionally not a runnable maintainer guide for the original source checkout.

## What The Repository Shows

The repository includes a long-form training script that:

- builds a small PaLM language model,
- trains on the enwik8 byte-level corpus,
- uses `Accelerator` for device handling,
- uses `Lion` from `lion_pytorch`,
- validates on a held-out split,
- and periodically generates text samples.

## Why The Original Training Flow Is Reference-Only

- The data file is large and the training loop is long-running.
- The repository metadata does not declare `lion-pytorch`, even though the script imports it.
- The script is useful as evidence for model construction and optimizer choice, but it is not the default runtime workflow for this skill.

## Distilled Recipe

If you intentionally want the full pretraining path, the workflow is conceptually:

1. Prepare the enwik8 corpus and the train/validation byte split.
2. Build a causal `PaLM` with byte-level vocabulary sizing.
3. Train with the package's parameter partitioning, keeping base parameters separate from any LoRA scope.
4. Use an optimizer appropriate for the script's architecture and scale.
5. Validate on a held-out slice and periodically sample generations.

## Tiny Alternative For Future Agents

For ordinary agent use, prefer the bundled smoke script instead of the long training loop.

- It checks the transformer loss path.
- It checks logits and embeddings.
- It checks generation suffix length.
- It checks optional LoRA scope wiring.

That is enough to confirm the API shape without committing to the expensive source recipe.

## Practical Notes

- The full recipe is byte-level and therefore does not require a tokenizer in the usual subword sense.
- The original script uses the external `Lion` optimizer, so a faithful rerun needs the extra dependency.
- The original script's defaults are tuned for a long training run, not for smoke verification.
