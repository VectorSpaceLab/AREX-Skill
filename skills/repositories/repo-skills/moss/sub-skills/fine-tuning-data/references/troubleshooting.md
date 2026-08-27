# MOSS fine-tuning and data troubleshooting

## Missing train/val files

**Symptoms**: file-not-found errors for `train.jsonl`, `val.jsonl`, `train_data`,
or `val_data`.

**Recovery**

- Provide `train.jsonl` and `val.jsonl` in the data directory, or pre-existing
  cached tensor files named exactly as the loader expects.
- Use separate train and validation files; prompt-only JSONL is not enough.
- Run `scripts/validate_sft_json.py` on the JSONL before tokenization.

## Malformed record schema

**Symptoms**: KeyError on `chat`, `turn_1`, `Human`, `MOSS`, etc.; validator
reports missing markers.

**Recovery**

- Ensure each record has `conversation_id`, `meta_instruction`, `num_turns`, and
  `chat`.
- Ensure turns are named `turn_1`, `turn_2`, ... up to `num_turns`.
- Include all five turn fields: `Human`, `Inner Thoughts`, `Commands`, `Tool
  Responses`, and `MOSS`.
- Preserve exact marker tokens, including `<eoh>`, `<eot>`, `<eoc>`, `<eor>`,
  and `<eom>`.

## Plugin data issues

**Symptoms**: plugin records train as plain chat, tool outputs affect loss, or
commands are missing.

**Recovery**

- Use `--expect-plugin` with the validator for plugin files.
- Confirm commands contain supported forms such as `Search(`, `Calculate(`,
  `Solve(`, or `Text2Image(`.
- Keep tool outputs inside `<|Results|>:` and `<eor>` so no-loss spans can be
  computed correctly by the loader.

## Token length over 2048

**Symptoms**: later turns silently disappear from cached data, or long samples
produce fewer training examples than expected.

**Recovery**

- The loader breaks out when adding a turn would exceed 2048 tokens.
- Split long conversations, shorten meta instructions only with care, or reduce
  per-sample turns.
- Use the actual MOSS tokenizer for precise length checks after JSON schema
  validation.

## Tokenizer/checkpoint failures

**Symptoms**: `AutoTokenizer.from_pretrained` or `AutoModelForCausalLM` fails,
remote code is not trusted, or EOS ids mismatch.

**Recovery**

- Use a complete MOSS base checkpoint or Hugging Face id.
- Pass `trust_remote_code=True` where appropriate.
- Preserve EOS mapping to `<eom>` id 106068 for SFT.
- Read the model-runtime troubleshooting reference for import/checkpoint issues.

## DeepSpeed/Accelerate failures

**Symptoms**: missing DeepSpeed plugin/config, wrong process count, NCCL errors,
OOM during ZeRO init, or checkpoint save failures.

**Recovery**

- Install and verify training dependencies intentionally; the base requirements
  alone may not include DeepSpeed.
- Generate or edit an Accelerate config with the bundled `plan_finetune_command.py` helper so `num_processes` matches available GPUs.
- Lower per-GPU batch sizes before disabling gradient checkpointing.
- Use isolated output and log directories with sufficient disk space.
- Treat full training as a scheduled multi-GPU job, not an interactive smoke
  check.

## Data privacy and licensing

The public README notes honesty data was removed because it contained private
information. Do not reintroduce private conversation data into SFT files without
review. Respect the separate data license before redistribution or commercial
use.
