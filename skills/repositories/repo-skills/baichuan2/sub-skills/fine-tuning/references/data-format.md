# Supervised Training Data Format

Baichuan2 supervised fine-tuning expects a JSON file containing a top-level list. Each item is a conversation record with a `conversations` list. Each message in `conversations` has:

- `from`: role name. Use `human` for user turns. Use `gpt` or `assistant` for assistant turns.
- `value`: message text.

Optional fields such as `id` are allowed and ignored by the trainer.

## Minimal record

```json
[
  {
    "id": "example-1",
    "conversations": [
      {"from": "human", "value": "Write a short poem about the sea."},
      {"from": "gpt", "value": "Waves fold silver into foam..."},
      {"from": "human", "value": "Make it one sentence."},
      {"from": "gpt", "value": "The moon folds silver waves into a single quiet song."}
    ]
  }
]
```

The public example that motivated this schema is a multi-turn Belle-style chat dataset sampled and converted to this list-of-conversations layout. It demonstrates formatting only; it is not evidence that a specific downstream fine-tune will improve model quality.

## Role and turn rules

Recommended validation policy:

1. Top-level value is a non-empty list.
2. Every record is an object with `conversations` as a non-empty list.
3. Every message is an object with string `from` and string `value`.
4. Conversations start with a human turn and normally alternate human/assistant.
5. The final turn should be an assistant response so the record contains supervised target text.
6. Empty or whitespace-only message values should be reviewed and usually rejected unless you intentionally model empty outputs.
7. Unknown non-human roles are risky because the trainer treats every non-human role as assistant text. Normalize roles before training.

Use the bundled validator before training. Its defaults are source-compatible: non-alternating turns and empty strings are warnings, not hard failures. For a stricter production gate, add `--require_alternating` and `--no-allow_empty_values`.

```bash
python scripts/validate_training_data.py \
  --data_path /data/baichuan2_sft.json
```

## Tokenization and labels

The bundled trainer preserves the repository training convention:

- Human turns are prefixed by the Baichuan user marker token id `195`.
- Assistant turns are prefixed by the assistant marker token id `196`.
- Text is encoded with the Baichuan tokenizer using `use_fast=False` and `trust_remote_code=True`.
- User text tokens are masked with `ignore_index=-100` so they do not contribute to ordinary language-model loss.
- Assistant text tokens are labels and therefore train the model.
- An EOS token is appended at the end of the sequence.
- Sequences are truncated to `model_max_length` and right padded with the tokenizer pad token.
- The attention mask is `input_ids != pad_token_id`.

The original trainer labels the user marker position with EOS while masking the human text. The bundled trainer keeps that behavior by default for compatibility. If you are doing a controlled training-method experiment, record any deviation from this label construction.

## Truncation risks

`model_max_length=512` is the documented example value. Multi-turn samples can exceed it. Truncation can remove late assistant targets or cut a response mid-answer, causing poor supervision.

When a tokenizer is available, estimate truncation before launching DeepSpeed:

```bash
python scripts/validate_training_data.py \
  --data_path /data/baichuan2_sft.json \
  --tokenizer_name_or_path baichuan-inc/Baichuan2-7B-Base \
  --model_max_length 512 \
  --max_records 1000
```

If many samples are truncated:

- increase `model_max_length` if GPU memory allows;
- filter or chunk very long conversations;
- lower `per_device_train_batch_size` and increase `gradient_accumulation_steps`;
- inspect whether long records have useful assistant targets near the end.

## Data validation failures to fix before training

- Top-level JSON object instead of list: wrap records in a list.
- OpenAI-style `messages` with `role`/`content`: convert to `conversations` with `from`/`value`.
- Role names `user`/`assistant`: normalize `user` to `human`; `assistant` is accepted by the bundled scripts but `gpt` matches the reference sample.
- Consecutive assistant turns: merge them or insert the missing human turn only if the semantics are correct.
- Last turn is human: remove it or add the intended assistant answer.
- Non-string values: convert to text deliberately; do not rely on JSON coercion.
