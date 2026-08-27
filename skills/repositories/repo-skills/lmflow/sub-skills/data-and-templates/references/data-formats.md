# LMFlow Data Formats

## Overview

LMFlow datasets are JSON objects with a top-level `type` and an `instances` array. The dataset directory form is a folder of one or more `.json` files. For training-style workflows, each JSON file in a dataset directory should describe the same LMFlow type.

## Common Top-Level Shape

```json
{
  "type": "text2text",
  "instances": [
    { "input": "Question", "output": "Answer" }
  ]
}
```

## Supported Types

| Type | Required instance keys | Typical use |
| --- | --- | --- |
| `text_only` | `text` | Raw text fine-tuning or simple inference inputs. |
| `text2text` | `input`, `output` | Paired prompt/response or instruction-following data. |
| `conversation` | `messages` | ShareGPT-style dialogue data, optionally with `system`, `tools`, and `conversation_id`. |
| `paired_conversation` | `chosen`, `rejected` | Preference comparisons using two full conversations. |
| `paired_text_to_text` | `prompt`, `chosen`, `rejected`, `margin` | Pairwise preference data for DPO-style workflows. |
| `text_to_textlist` | `input`, `output` list | Reward-model inference and ranking-style tasks. |
| `text_to_scored_textlist` | `input`, `output` list of `{score,text}` | Reward-model training and RL-style scoring workflows. |
| `float_only` | numeric values | Specialized numeric datasets. |
| `image_text` | image/text fields | Multimodal workflows. |

## Conversation Details

A conversation instance may include:

- `conversation_id`: optional tracking id.
- `system`: optional system prompt string.
- `tools`: optional list of tool descriptions.
- `messages`: ordered list of `{role, content}` items.

Rules:

- conversations should start with a user message;
- user/assistant turns should alternate;
- the content should not be empty;
- if the final user turn is unmatched, LMFlow may trim it during preprocessing.

## Preference Data Notes

For alignment workflows, the most common layouts are:

- `paired_text_to_text`: one prompt with chosen/rejected answers;
- `paired_conversation`: a full chosen and rejected conversation;
- `text_to_scored_textlist`: multiple candidate responses with scores.

These are the inputs used by DPO, DPOv2, iterative DPO, and reward-model workflows.

## Directory Layout

For training, LMFlow commonly expects a directory of JSON files such as:

```text
my_dataset/
  train.json
  valid.json
  extra.json
```

All files in one directory should agree on the top-level `type` unless the workflow explicitly separates them.
