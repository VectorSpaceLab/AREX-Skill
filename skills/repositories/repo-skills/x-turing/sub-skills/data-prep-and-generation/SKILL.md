---
name: "data-prep-and-generation"
description: "Prepare, validate, convert, and self-generate xTuring datasets for
  text, instruction, and preference workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-prep-and-generation

Use this sub-skill when you need to build or validate xTuring data for text completion, instruction tuning, preference/DPO training, or API-backed self-instruct generation.

## Route here for

- `TextDataset`, `InstructionDataset`, `PreferenceDataset`, and `ListPromptTemplate`
- JSON, JSONL, and saved-dataset layouts for the supported dataset classes
- Alpaca-to-xTuring conversion and dataset persistence
- Self-instruct generation through `InstructionDataset.generate_dataset(...)` and `generate_dataset_from_dir(...)`
- OpenAI, Cohere, and Claude wrapper caveats used by generation helpers
- Dataset schema troubleshooting before training or evaluation

## Route away

- Model loading, model registry choices, or generation from a saved model → `models-and-inference`
- Fine-tuning, LoRA, INT8, or DPO training loops → `training-and-alignment`
- CLI, API server, or UI serving → `cli-api-ui`
- Evaluation harnesses or result persistence → `evaluation`
- `Text2ImageDataset` is not implemented and should not be used as a data route

## Read first

- `references/data-formats.md` for supported schemas, constructors, JSONL shapes, and save behavior
- `references/self-instruct-and-apis.md` for seed-task format, cache files, wrapper behavior, and text-extraction caveats
- `references/troubleshooting.md` for schema assertions, malformed input, missing dependencies, and API retry failures

## Skill-owned scripts

- `scripts/convert_alpaca_json.py` — convert Alpaca JSON into a saved Hugging Face dataset compatible with `InstructionDataset`
- `scripts/validate_xturing_dataset.py` — validate a candidate dataset against the text, instruction, or preference schema

## Typical workflow

1. Inspect the raw file and decide whether it is text, instruction, or preference data.
2. Validate the schema and fix missing or extra fields before conversion.
3. Convert or load the data into a Hugging Face dataset and save it to disk when needed.
4. Use self-instruct generation only when you have a supported text-generation API wrapper and the required credentials.
5. Revisit the troubleshooting guide if the constructor, JSONL loader, or API helper rejects the data.

## Cross-links

- If the data is valid but training fails later, switch to `training-and-alignment`.
- If the request is actually about model selection or inference behavior, switch to `models-and-inference`.
