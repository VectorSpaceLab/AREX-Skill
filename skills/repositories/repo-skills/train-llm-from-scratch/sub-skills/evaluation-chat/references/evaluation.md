# Evaluation reference

This reference covers the repo's post-training evaluator: GSM8K greedy accuracy, sample generations, JSONL append rows, and stage-table rendering.

## What the evaluator does

The evaluator loads one checkpoint, prompts GSM8K questions with the chat template, generates deterministic completions, parses the final numeric answer, and compares it to the gold answer. The headline comparison is a single table across checkpoints such as Base, SFT, DPO, PPO, and GRPO.

Evaluation is model-based and data-based. It can require a real checkpoint, a working torch device, the `datasets` package, and local/cache/network access to GSM8K. Use the bundled command builder first when the user only needs a command plan.

## Dry-run command builder

From this sub-skill directory, use:

```bash
python scripts/build_eval_command.py --ckpt checkpoints/sft.pt --label sft --limit 200 --append logs/stage_table.jsonl
python scripts/build_eval_command.py --table logs/stage_table.jsonl
```

For multiple stage rows:

```bash
python scripts/build_eval_command.py \
  --stage base_pretrained=checkpoints/base_pretrained.pt \
  --stage sft=checkpoints/sft.pt \
  --stage dpo=checkpoints/dpo.pt \
  --stage ppo=checkpoints/ppo.pt \
  --stage grpo=checkpoints/grpo.pt \
  --limit 200 --append logs/stage_table.jsonl --render-table
```

The helper prints commands only. It does not check that checkpoints or datasets exist.

## Evaluator command shape

Run from a checkout or environment where the repo package is importable:

```bash
PYTHONPATH=. python scripts/eval_post_training.py \
  --ckpt checkpoints/sft.pt \
  --label sft \
  --limit 200 \
  --split test \
  --max_new_tokens 300 \
  --device cuda \
  --samples 3 \
  --append logs/stage_table.jsonl
```

Render an existing JSONL table without loading a model:

```bash
PYTHONPATH=. python scripts/eval_post_training.py --table logs/stage_table.jsonl
```

## `eval_post_training.py` flags

| Flag | Meaning | Typical use |
|---|---|---|
| `--ckpt PATH` | Checkpoint to evaluate. Required unless `--table` is used. | Use a base, SFT, DPO, PPO, GRPO, or reward checkpoint whose backbone matches its stored config. |
| `--label TEXT` | Stage label stored in the output row and printed in logs. Default is `model`. | Use `base_pretrained`, `sft`, `dpo`, `ppo`, or `grpo` for stage tables. |
| `--limit N` | Maximum GSM8K examples to evaluate. Default is 200. | Start small for smoke checks; raise only when runtime and data access are acceptable. |
| `--split NAME` | GSM8K split. Default is `test`. | Use a consistent split for all rows in one table. |
| `--max_new_tokens N` | Generation budget per question. Default is 300. | Increase for long reasoning if context length leaves room; lower for fast smoke checks. |
| `--device DEVICE` | Torch device. Defaults to CUDA when available, otherwise CPU. | Set explicitly when avoiding CUDA allocation or diagnosing device mismatch. |
| `--samples N` | Number of qualitative question/gold/response examples to print. Default is 3. | Use `0` for quiet table-only row generation. |
| `--append PATH` | Append one JSONL result row with label, accuracy, correct, and n. | Use one shared file for a stage table. |
| `--table PATH` | Print a table from an existing JSONL file and exit. | No checkpoint, dataset, or model load is needed. |

## Stage-table workflow

1. Pick a fixed GSM8K split, limit, generation budget, and device.
2. Evaluate each stage with greedy decoding and append to the same JSONL file.
3. Render the JSONL file as the stage table.
4. Compare relative movement across stages; modest absolute GSM8K scores are expected for small from-scratch models.

Example dry-run plan:

```bash
PYTHONPATH=. python scripts/eval_post_training.py --ckpt checkpoints/base_pretrained.pt --label base_pretrained --limit 200 --split test --max_new_tokens 300 --device cuda --samples 3 --append logs/stage_table.jsonl
PYTHONPATH=. python scripts/eval_post_training.py --ckpt checkpoints/sft.pt --label sft --limit 200 --split test --max_new_tokens 300 --device cuda --samples 3 --append logs/stage_table.jsonl
PYTHONPATH=. python scripts/eval_post_training.py --ckpt checkpoints/dpo.pt --label dpo --limit 200 --split test --max_new_tokens 300 --device cuda --samples 3 --append logs/stage_table.jsonl
PYTHONPATH=. python scripts/eval_post_training.py --ckpt checkpoints/ppo.pt --label ppo --limit 200 --split test --max_new_tokens 300 --device cuda --samples 3 --append logs/stage_table.jsonl
PYTHONPATH=. python scripts/eval_post_training.py --ckpt checkpoints/grpo.pt --label grpo --limit 200 --split test --max_new_tokens 300 --device cuda --samples 3 --append logs/stage_table.jsonl
PYTHONPATH=. python scripts/eval_post_training.py --table logs/stage_table.jsonl
```

## Generation and scoring behavior

- GSM8K prompts are encoded as a chat prompt ending with an assistant header.
- `gsm8k_accuracy(...)` calls length-bucketed generation because the educational Transformer has no padding-aware attention mask.
- Evaluation uses greedy decoding by default for comparable numbers. Greedy means argmax-style generation with `top_k=1`; it is not a sampling-quality setting.
- Generation stops on the end-of-text token id `50256` and decodes only ordinary tokenizer ids below that value.
- If a prompt plus requested generation exceeds the model context length, generation budget is clamped by the model's context capacity.

## Answer extraction priority

The answer parser is intentionally tolerant because small models may not follow the exact format. It extracts the first usable numeric answer in this priority order:

1. A number inside `<answer> ... </answer>`.
2. A GSM8K-style answer after `####`.
3. The last number anywhere in the text.
4. `None` if no number can be parsed.

Numbers may include a sign, dollar sign, thousands commas, or decimals. Numeric comparison uses a small absolute float tolerance.

Use the bundled parser helper for quick diagnosis:

```bash
python scripts/check_answer_format.py --text '<think>13+29</think><answer>42</answer>' --gold 42
python scripts/check_answer_format.py --text 'Reasoning... #### 18' --gold 18
python scripts/check_answer_format.py --text 'wrong tag <answer></answer> but last number is 7' --gold 7
```

## Verifier reward behavior

The GSM8K verifier is correctness-dominant:

- `+1.0` if the parsed numeric answer matches the gold answer.
- `+0.2` if there is exactly one well-formed `<answer>...</answer>` block.
- The reward is clipped at `1.2`.

Consequences:

- A correct untagged answer can be correct for accuracy but miss the small format bonus.
- A wrong answer in a well-formed tag can receive only the format bonus; it is still wrong for accuracy.
- Multiple answer tags fail the format-bonus check. Extraction checks the first answer block first; if that block has no parseable number, later numbers may still be selected only through the `####` or last-number fallback.
- A syntactically matched but empty answer tag counts as an answer block for the format-bonus test; it does not provide correctness unless a fallback number also matches gold.
- The verifier is not a semantic judge. It only checks numeric extraction and comparison.

## Reward checkpoints in evaluation

A reward-model checkpoint can contain reward-head keys that are not part of the language-model backbone. The evaluator/backbone loader filters checkpoint keys to the Transformer state, so extra reward-head keys are ignored for generation. This is useful for diagnosing checkpoints, but the reward head itself is not used to compute GSM8K verifier accuracy.
