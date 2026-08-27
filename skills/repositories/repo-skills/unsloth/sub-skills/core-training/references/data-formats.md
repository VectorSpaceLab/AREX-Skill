# Data Formats For Core Training

Use this reference to shape small local samples and configs before producing Unsloth Core training code. Validate planned files with `scripts/validate_training_config.py` before model loading or training.

## Config Shape

The bundled validator accepts YAML or JSON with these sections:

```yaml
model:
  name: unsloth/Llama-3.2-1B-Instruct
  loader: FastLanguageModel
  max_seq_length: 2048
  load_in_4bit: true
  load_in_8bit: false
  load_in_16bit: false
  full_finetuning: false
  trust_remote_code: false

lora:
  r: 16
  lora_alpha: 16
  lora_dropout: 0.0
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
  modules_to_save: []
  finetune_last_n_layers: null

data:
  path: train.jsonl
  format: chat_jsonl
  chat_template: chatml
  messages_field: messages
  role_field: role
  content_field: content
  role_aliases:
    user: [user, human, input]
    assistant: [assistant, gpt, output]
    system: [system, developer]

training:
  output_dir: outputs
  per_device_train_batch_size: 2
  gradient_accumulation_steps: 4
  learning_rate: 0.0002
  max_steps: 60
  packing: false
  report_to: none
```

Validation expectations:

- `model.name` is required.
- `model.loader` should be one of `FastLanguageModel`, `FastModel`, `FastVisionModel`, `FastTextModel`, or `FastSentenceTransformer`.
- Only one quantization flag should be true.
- `full_finetuning=true` should not be combined with quantization flags or a LoRA section intended to add adapters.
- `max_seq_length`, LoRA rank, batch size, gradient accumulation, and learning rate should be positive.
- `trust_remote_code=true` is allowed but should trigger a user-facing risk note.

## Chat JSONL

Recommended row shape:

```json
{"messages":[{"role":"system","content":"You are concise."},{"role":"user","content":"Hi"},{"role":"assistant","content":"Hello."}]}
```

Alternative ShareGPT-style row shape:

```json
{"conversations":[{"from":"human","value":"Hi"},{"from":"gpt","value":"Hello."}]}
```

Mapping guidance:

- Use `messages_field: messages` for OpenAI-style rows and `messages_field: conversations` for ShareGPT-style rows.
- Use `role_field: role` and `content_field: content` for OpenAI-style rows.
- Use `role_field: from` and `content_field: value` for ShareGPT-style rows.
- Role aliases should map user-like values to `user`, assistant-like values to `assistant`, and system/developer-like values to `system`.
- Each conversation should contain at least one user message and one assistant message for SFT.
- Message `content` should be non-empty text for text-only training; multimodal content lists require a vision-capable loader and collator.

## Applying Chat Templates

Use `get_chat_template` to patch a tokenizer and then apply `tokenizer.apply_chat_template` to each conversation.

```python
tokenizer = get_chat_template(
    tokenizer,
    chat_template="chatml",
    mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"},
)
```

Notes:

- If the dataset uses custom keys, adapt the `mapping` and/or normalize records before calling the tokenizer.
- Some templates reject invalid role alternation; validate tiny samples before launching training.
- Gemma-family tokenizers may be remapped from `chatml` to Gemma-specific templates by Unsloth.
- For response-only SFT, apply `train_on_responses_only` after constructing the trainer.

## Plain Text And Raw Text

`RawTextDataLoader` extracts text from these extensions:

| Extension | Interpretation | Extraction |
| --- | --- | --- |
| `.txt` | plain text | entire file |
| `.md` | markdown | entire file |
| `.json` / `.jsonl` | JSON lines | first string field from `text`, `content`, `message`, `body`, `description`, or `prompt` |
| `.csv` | CSV rows | first non-empty text-like column from the same field list |

Constraints:

- `chunk_size` must be positive.
- `stride` must be lower than `chunk_size`.
- Empty or whitespace-only files are rejected.
- Tokenized chunks include `input_ids`, `attention_mask`, and `labels`.
- Text chunks include only `text`, which works with `dataset_text_field="text"`.

## Vision And Multimodal Records

Vision-language training usually uses a processor and `UnslothVisionDataCollator`. Keep this sub-skill focused on Core wiring; route Studio UI dataset flows to `../studio-runtime/SKILL.md`.

Recommended planning checks:

- Every referenced local image/video path exists before trainer construction.
- The model is loaded with `FastVisionModel` or `FastModel`, not `FastLanguageModel`, unless using `text_only=True` intentionally.
- `SFTTrainer` uses `processing_class=processor` and a vision data collator, not `dataset_text_field` alone.
- Packing/padding-free behavior may be disabled for processor-based or VLM workflows.

## Dataset Field Errors To Catch Early

- Missing `messages`, `conversations`, or configured text field.
- Message rows that are not lists of dictionaries.
- Missing role/content keys.
- Unknown roles after alias mapping.
- Assistant-only or user-only conversations.
- Empty content strings.
- Raw-text config with `stride >= chunk_size`.
- `dataset_text_field` set when the dataset will be converted with a formatting function instead.
