---
name: generative-workflows
description: "Use Simple Transformers language modeling, language generation,
  T5, Seq2Seq, ConvAI, and text-to-text workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simple Transformers Generative Workflows Sub-skill

Use this sub-skill for language-model fine-tuning or training from scratch,
free-form generation, T5 text-to-text tasks, generic Seq2Seq encoder/decoder
models, and ConvAI chatbot-style workflows.

## Owns

- `LanguageModelingModel` / `LanguageModelingArgs` / `GenerationArgs`.
- `LanguageGenerationModel` / `LanguageGenerationArgs`.
- `T5Model` / `T5Args` for prefix-based text-to-text tasks.
- `Seq2SeqModel` / `Seq2SeqArgs` for encoder-decoder and separate encoder/decoder setups.
- `ConvAIModel` / `ConvAIArgs` for conversational training and interaction.
- Text, CSV/DataFrame, prefix/input/target, and conversation data validation.

## Route elsewhere

- Ordinary binary/multiclass/multilabel/regression classification: [classification](../classification/SKILL.md).
- Extractive QA or NER: [token-and-qa](../token-and-qa/SKILL.md).
- Dense retrieval, representations, and BEIR/MSMARCO: [retrieval-representation](../retrieval-representation/SKILL.md).

## Read first

1. [API reference](references/api-reference.md) for constructors and methods.
2. [Data formats](references/data-formats.md) before preparing LM/T5/Seq2Seq/ConvAI inputs.
3. [Workflows](references/workflows.md) for CPU-safe recipes and constructor choices.
4. [Troubleshooting](references/troubleshooting.md) for model downloads, text-to-text prefixes, tokenizer/from-scratch settings, and compatibility import issues.

## Validation helper

```bash
python scripts/validate_generative_data.py --task lm-text --input train.txt
python scripts/validate_generative_data.py --task t5-csv --input t5.csv
python scripts/validate_generative_data.py --task seq2seq-csv --input pairs.csv
python scripts/validate_generative_data.py --task t5-predict-lines --input predict.txt
python scripts/validate_generative_data.py --task convai-json --input convai.json
```

The helper checks data shape only. It does not download models, train, generate,
or open network connections.

## Key decisions

- **Language modeling:** pretrained fine-tuning needs `model_name`; training from scratch needs `model_name=None`, `train_files`, and `vocab_size`/tokenizer settings.
- **T5:** training/eval DataFrames use `prefix`, `input_text`, `target_text`; prediction strings must already include `"prefix: "`.
- **Seq2Seq:** either pass `encoder_decoder_type`/`encoder_decoder_name` for unified models like BART, or pass separate `encoder_type`, `encoder_name`, and `decoder_name`.
- **Generation:** keep `max_length`, `max_new_tokens`, `do_sample`, `top_k`, `top_p`, `temperature`, and `num_return_sequences` explicit.
- **ConvAI:** expect additional compatibility and data-shape risk because upstream utility imports use old Transformers cache helpers.

## Verification status

Constructor signatures were inspected for Simple Transformers 0.70.8. Native LM/Seq2Seq/T5 examples train or download models and are skipped by default; use validators and small cached-model smoke tests unless the user approves larger runs.
