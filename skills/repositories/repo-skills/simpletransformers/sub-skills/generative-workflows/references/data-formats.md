# Generative Data Formats

## Language modeling text

Use plain text files for `LanguageModelingModel.train_model()` and `train_files`. Keep one document or sentence per line for line-by-line style runs. For from-scratch tokenizers, provide enough text and set `vocab_size`.

## T5 train/eval DataFrame

Columns:

| column | type | notes |
|---|---|---|
| `prefix` | string | task label such as `translate`, `summarize`, `binary classification` |
| `input_text` | string | source text; prefix separator is added when `preprocess_inputs=True` |
| `target_text` | string/int | target sequence |

Prediction is a list of strings that already include the prefix and separator:

```python
["summarize: long document text", "translate English to German: Good morning"]
```

## Seq2Seq train/eval DataFrame

Columns:

| column | type | notes |
|---|---|---|
| `input_text` | string | encoder/source text |
| `target_text` | string | decoder/target text |

Prediction is a list of source strings.

## Language generation input

`LanguageGenerationModel.generate()` uses prompts and generation args. Provide explicit decoding args to prevent surprising long or stochastic outputs.

## ConvAI data

ConvAI examples use conversation/personality-style data structures. Before training, make sure each conversation has a personality list and utterances/candidates/history shaped consistently with the selected model family.

## Validator

```bash
python scripts/validate_generative_data.py --task lm-text --input train.txt
python scripts/validate_generative_data.py --task t5-csv --input data.csv
python scripts/validate_generative_data.py --task seq2seq-csv --input data.csv
python scripts/validate_generative_data.py --task t5-predict-lines --input predict.txt
python scripts/validate_generative_data.py --task convai-json --input convai.json
```
