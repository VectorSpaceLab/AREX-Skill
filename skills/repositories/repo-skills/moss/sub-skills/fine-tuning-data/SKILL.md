---
name: fine-tuning-data
description: "Routes MOSS SFT data and fine-tuning tasks for conversation
  schemas, plugin transcripts, no-loss spans, DeepSpeed config, and safe
  validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MOSS fine-tuning and SFT data

Use this sub-skill when a task asks about MOSS SFT data formats, plugin/no-plugin
conversation records, user prompt files, the `SFTDataset` loader, no-loss spans,
Accelerate/DeepSpeed configuration, or fine-tuning command construction.

## Read this when

- The user needs to prepare or validate `train.jsonl` and `val.jsonl` for MOSS
  supervised fine-tuning.
- The task mentions `finetune_moss.py`, `SFTDataset`, `no_loss_spans`,
  `configs/sft.yaml`, `Accelerator`, `DeepSpeed`, or MOSS plugin data.
- You need to distinguish no-plugin conversations from plugin-augmented records
  with `Inner Thoughts`, `Commands`, and `Tool Responses`.
- You need a safe data validator without tokenizing or training.
- You are debugging missing data files, malformed JSON, length overflows,
  tokenizer/checkpoint issues, DeepSpeed config, or multi-GPU OOM.

## Route elsewhere

- For model class imports and checkpoint/runtime constraints, read
  [../model-runtime/SKILL.md](../model-runtime/SKILL.md).
- For chat prompt formatting and inference commands, read
  [../inference/SKILL.md](../inference/SKILL.md).
- For API/UI serving, read [../serving/SKILL.md](../serving/SKILL.md).
- For shared dependency and license guidance, read
  [../../references/install-and-dependencies.md](../../references/install-and-dependencies.md).

## Operating workflow

1. **Identify the data shape.** The training loader expects a data directory
   containing `train.jsonl` and `val.jsonl`, or cached `train_data`/
   `train_no_loss_spans` and `val_data`/`val_no_loss_spans` tensors.
2. **Validate records before tokenization.** Each conversation record needs
   `conversation_id`, `meta_instruction`, `num_turns`, and a `chat` object with
   `turn_1`, `turn_2`, ... entries. Every turn includes `Human`, `Inner
   Thoughts`, `Commands`, `Tool Responses`, and `MOSS` strings with MOSS marker
   tokens.
3. **Understand no-loss spans.** The loader masks the meta instruction and
   plugin tool response payload spans with `-100` labels, while keeping format
   tokens around plugin responses trainable.
4. **Keep training-scale execution explicit.** Full fine-tuning uses PyTorch,
   Accelerate, mixed precision FP16, DeepSpeed ZeRO-3 in the provided config,
   and multiple GPUs. Do not run it as a validation check.
5. **Use the bundled validator.** Run
   [scripts/validate_sft_json.py](scripts/validate_sft_json.py) against sample
   or prepared JSON/JSONL files before any tokenizer/model work.

## Safe validation examples

```bash
python path/to/moss/sub-skills/fine-tuning-data/scripts/validate_sft_json.py sample_conversation.json
python path/to/moss/sub-skills/fine-tuning-data/scripts/validate_sft_json.py plugin_sample.json --expect-plugin --json
python path/to/moss/sub-skills/fine-tuning-data/scripts/validate_sft_json.py train.jsonl --sample-limit 100
```

The helper only checks structure and markers. It does not download checkpoints,
instantiate tokenizers, or run training.

## References

- [references/data-formats.md](references/data-formats.md) — conversation JSON,
  user prompt files, plugin transcript markers, and no-loss span rules.
- [references/workflows.md](references/workflows.md) — data preparation,
  validation, cache behavior, Accelerate/DeepSpeed config, and training command
  planning.
- [references/troubleshooting.md](references/troubleshooting.md) — malformed
  records, missing files, token length, tokenizer/checkpoint, DeepSpeed, and
  GPU-memory failures.
- [scripts/validate_sft_json.py](scripts/validate_sft_json.py) — safe schema and
  marker validator.

## Answering checklist

- Separate schema validation from full tokenization/training.
- Name whether data is plugin-augmented or no-plugin.
- Preserve MOSS special markers exactly when explaining formats.
- Treat records exceeding 2048 tokens as a training-loader issue, not a JSON
  schema issue alone.
- Warn that full fine-tuning is a multi-GPU, checkpoint- and data-dependent
  workload.
