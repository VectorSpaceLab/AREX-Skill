# Preference Data Formats

## Purpose

Read this when mapping local records into Axolotl preference-tuning datasets or before running the bundled JSON/JSONL checker. The examples are small shape examples, not training-quality datasets.

## Run The Bundled Checker

Use the helper for quick local JSON or JSONL shape checks before calling Axolotl preprocessing:

```bash
python scripts/check_preference_dataset.py --mode dpo --input sample.jsonl
python scripts/check_preference_dataset.py --mode kto --input sample.jsonl
```

The helper does not import Axolotl, load models, download data, or train. It validates small local fixtures for missing fields, empty values, identical chosen/rejected values, and KTO label shape.

Useful options:

```bash
python scripts/check_preference_dataset.py --mode dpo --input sample.jsonl \
  --chosen-field better --rejected-field worse --require-prompt

python scripts/check_preference_dataset.py --mode kto --input sample.jsonl \
  --prompt-field question --completion-field answer --label-field is_good
```

## DPO, IPO, ORPO, And SimPO Pair Shape

DPO, IPO, ORPO, and SimPO all start from paired preference data: one prompt context plus a preferred response and a rejected response. The canonical transformed keys are `prompt`, `chosen`, and `rejected`.

Simple text pair:

```json
{"prompt": "Explain LoRA briefly.", "chosen": "LoRA adapts low-rank matrices.", "rejected": "I cannot help."}
```

Chat-template pair with existing history:

```json
{
  "messages": [
    {"role": "system", "content": "Be concise."},
    {"role": "user", "content": "Explain LoRA briefly."}
  ],
  "chosen": {"role": "assistant", "content": "LoRA trains small low-rank adapters."},
  "rejected": {"role": "assistant", "content": "LoRA is unrelated to models."}
}
```

Argilla-style conversation pair:

```json
{
  "chosen": [
    {"role": "user", "content": "Explain LoRA briefly."},
    {"role": "assistant", "content": "LoRA trains low-rank adapters."}
  ],
  "rejected": [
    {"role": "user", "content": "Explain LoRA briefly."},
    {"role": "assistant", "content": "LoRA changes the dataset."}
  ]
}
```

For `chat_template.default`, map nonstandard fields in YAML instead of renaming the source data by hand:

```yaml
datasets:
  - path: my-preference-data
    split: train
    type: chat_template.default
    field_messages: conversation
    field_chosen: better
    field_rejected: worse
    message_property_mappings:
      role: speaker
      content: text
    roles:
      user: [human]
      assistant: [agent]
      system: [system]
```

For custom text fields, use a dictionary `type` mapping:

```yaml
datasets:
  - path: my-preference-data
    split: train
    type:
      field_prompt: prompt
      field_system: system
      field_chosen: chosen
      field_rejected: rejected
      prompt_format: "{prompt}"
      chosen_format: "{chosen}"
      rejected_format: "{rejected}"
```

## DPO Family Type Names

Common DPO-family dataset `type` values include:

- `chat_template.default` for chat history plus selected chosen/rejected assistant messages.
- `chat_template.argilla_chat` for full chosen and rejected conversations.
- `chatml.intel`, `chatml.prompt_pairs`, `chatml.argilla`, `chatml.argilla_chat`, `chatml.icr`, and `chatml.ultra` for documented ChatML pair formats.
- `llama3.intel`, `llama3.prompt_pairs`, `llama3.argilla`, `llama3.argilla_chat`, `llama3.icr`, and `llama3.ultra` for Llama 3 formatting variants.
- `zephyr.nectar` for ranked answer arrays.
- A dictionary `type` with `field_prompt`, `field_chosen`, `field_rejected`, and optional formatting keys for user-defined pair data.

The `type` value resolves under the selected RL method's prompt-strategy namespace. For example, DPO-like pair strategies produce `prompt`, `chosen`, and `rejected` text for the trainer.

## KTO Unpaired Shape

KTO is not DPO with a missing rejected response. It uses unpaired completions with a desirable/undesirable label.

Canonical KTO record:

```json
{"prompt": "Explain LoRA briefly.", "completion": "LoRA trains small adapter matrices.", "label": true}
```

Custom KTO field mapping:

```yaml
rl: kto
remove_unused_columns: false
datasets:
  - path: my-kto-data
    split: train
    type:
      field_prompt: question
      field_completion: answer
      field_label: is_good
      prompt_format: "{prompt}"
      completion_format: "{completion}"
```

Accepted helper label values are JSON booleans, `0`/`1`, and common true/false strings such as `true`, `false`, `yes`, `no`, `desirable`, and `undesirable`. Prefer real JSON booleans in the training data when possible.

## KTO Type Names

Common KTO `type` values include:

- `chatml.argilla`, `chatml.argilla_chat`, `chatml.intel`, `chatml.prompt_pairs`, and `chatml.ultra`.
- `llama3.argilla`, `llama3.argilla_chat`, `llama3.intel`, `llama3.prompt_pairs`, and `llama3.ultra`.
- A dictionary `type` with `field_prompt`, `field_completion`, `field_label`, and optional formatting keys for user-defined data.

KTO prompt strategies write canonical `prompt`, `completion`, and `label` keys after transformation.

## ORPO Pair Notes

ORPO's `chat_template.argilla` path expects `chosen` and `rejected` conversations. The chosen and rejected histories should match through the prompt/history and differ at the final assistant answer. A `prompt` field can provide the single-turn user prompt when available.

Shape to prefer:

```json
{
  "system": "Optional system message.",
  "prompt": "Solve 2 + 2.",
  "chosen": [
    {"role": "user", "content": "Solve 2 + 2."},
    {"role": "assistant", "content": "4"}
  ],
  "rejected": [
    {"role": "user", "content": "Solve 2 + 2."},
    {"role": "assistant", "content": "5"}
  ]
}
```

For multi-turn rows, keep an even number of alternating user/assistant turns in `chosen` and `rejected`; the final assistant message is the preference target.

## Outcome Reward Model Data

Outcome reward models use pairwise data to train a sequence classifier. The common shape is a prompt context plus `chosen` and `rejected` responses:

```json
{"system": "Optional system message.", "input": "Explain LoRA.", "chosen": "Correct answer.", "rejected": "Incorrect answer."}
```

Config essentials:

```yaml
reward_model: true
model_type: AutoModelForSequenceClassification
num_labels: 1
datasets:
  - path: my-rm-data
    type: bradley_terry.chat_template
remove_unused_columns: false
pad_to_sequence_len: true
```

## Process Reward Model Data

Process reward models use `stepwise_supervised` data for token-level or step-level labels. Keep the data aligned with the configured step separator and maximum completion length.

Config essentials:

```yaml
process_reward_model: true
model_type: AutoModelForTokenClassification
num_labels: 2
datasets:
  - path: my-prm-data
    type: stepwise_supervised
    step_separator: "\n"
    max_completion_length: 512
```

Use PRM when the labels are about reasoning steps or intermediate process quality. Use outcome reward models when the label is about the whole answer.

## Preprocess Expectations

- `axolotl preprocess config.yaml` should load the dataset and config without model training.
- `axolotl preprocess config.yaml --debug` should show whether chat templates, chosen/rejected stripping, KTO completion fields, and labels look correct.
- The bundled checker catches only local record shape. It does not guarantee tokenizer compatibility, sequence fit, optional dependency availability, or full Axolotl runtime success.
