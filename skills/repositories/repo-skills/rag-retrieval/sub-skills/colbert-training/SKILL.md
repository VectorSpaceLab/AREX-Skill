---
name: colbert-training
description: "Train ColBERT-style late-interaction retrieval models with bundled
  RAG-Retrieval training snapshots, triplet JSONL data, ColBERT dimensions, and
  accelerate/FSDP launch configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ColBERT Training

Use this sub-skill when a user asks to train or fine-tune a ColBERT-style late-interaction retriever, especially for prompts such as “train ColBERT”, “fine-tune `BAAI/bge-m3` ColBERT”, “triplet data for ColBERT”, “what should `colbert_dim` be?”, or “`Reranker` with `model_type=colbert` is not working”.

This workflow uses bundled source-code training snapshots by default and treats the installed package’s ColBERT reranker route as unavailable unless the source has been updated to register a working `ColBERTRanker`. Use an external checkout only when the user explicitly wants current repository code.

## Quick Routing

1. Confirm the user has training dependencies installed and a triplet JSONL file; an external checkout is optional because this skill bundles the inspected training code snapshot.
2. Validate the JSONL and common argument choices before launching training:

   ```bash
   python sub-skills/colbert-training/scripts/validate_colbert_training_args.py \
     --data train.jsonl \
     --model-name-or-path BAAI/bge-m3 \
     --colbert-dim 1024 \
     --neg-nums 15
   ```

3. Choose the accelerate config by backbone family: BERT-like models use a `BertLayer` FSDP config; `BAAI/bge-m3`/XLM-RoBERTa-like models use an `XLMRobertaLayer` FSDP config.
4. Build a path-checked launch command with `scripts/build_colbert_training_command.py`, review it, then run bundled or explicitly selected checkout training.
5. If the user asks for packaged ColBERT inference through `Reranker`, redirect them to bundled/source-code scoring or an inference limitation note; do not claim installed `Reranker(..., model_type="colbert")` works.

## Reference Map

- [Data formats](references/data-formats.md): triplet JSONL schema, positive expansion, negative resampling, token length fields, and validation expectations.
- [Configuration](references/configuration.md): `train_colbert.py` arguments, `colbert_dim`, model/backbone choices, FSDP config selection, batches, logging, and checkpoint options.
- [Workflows](references/workflows.md): bundled launch shape, preflight validation sequence, saved model scoring, and inference caveats.
- [Troubleshooting](references/troubleshooting.md): dimension mismatch, insufficient negatives, model downloads, GPU/FSDP issues, memory, saved model loading, and packaged reranker limitations.
- [Validator script](scripts/validate_colbert_training_args.py): safe no-download JSONL and argument preflight helper.
- [Command builder](scripts/build_colbert_training_command.py): builds a path-checked `accelerate launch` command for a user-supplied checkout.

## Do Not Overclaim

RAG-Retrieval’s public `Reranker` mapping may mention `colbert`/`ColBERTRanker`, but the available ranker registry can omit a working `ColBERTRanker`. For trained ColBERT checkpoints, use the bundled/source-code training model class and scoring pattern unless the current source explicitly implements and registers package ColBERT inference.
