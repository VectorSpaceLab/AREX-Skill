# Token and QA Data Formats

## NER DataFrame

Use columns:

| column | type | notes |
|---|---|---|
| `sentence_id` | int/string group id | same value groups tokens into one sentence |
| `words` | string | one token per row |
| `labels` | string | tag such as `O`, `B-PER`, `I-ORG` |

For LayoutLM token classification, add `x0`, `y0`, `x1`, `y1` integer coordinate columns normalized to `[0, 1000]`.

## NER CoNLL text

One token per line, sentence boundary as a blank line. The first field is the word and the last field is the label.

```text
Harry B-PER
Potter I-PER
was O

Hogwarts B-LOC
```

For LayoutLM-style CoNLL, include the box coordinates as additional fields and keep the last field as the label only if your preprocessing expects that layout. Validate manually before training.

## NER prediction

Default prediction takes list of strings and splits on spaces:

```python
model.predict(["Ron is Harry's best friend"])
```

For custom tokenization, pass list-of-token-lists and `split_on_space=False`:

```python
model.predict([["Ron", "is", "Harry", "'s", "friend"]], split_on_space=False)
```

## QA train/eval format

Use a list of dictionaries or a JSON file containing that list:

```python
[
  {
    "context": "Mistborn was written by Brandon Sanderson.",
    "qas": [
      {
        "id": "q1",
        "question": "Who wrote Mistborn?",
        "is_impossible": false,
        "answers": [{"text": "Brandon Sanderson", "answer_start": 23}]
      }
    ]
  }
]
```

Training questions should have a single correct answer, or an empty answer list with `is_impossible=True`. Evaluation may contain multiple accepted answers.

## QA prediction format

Prediction omits gold answers and `is_impossible`:

```python
[
  {"context": "Vin is a Mistborn.", "qas": [{"id": "q0", "question": "What is Vin?"}]}
]
```

## QA lazy loading

Lazy QA training uses JSONL: one JSON object per line with the same context/qas structure. Lazy loading is for training; evaluation still loads in memory.

## Validation helper

```bash
python scripts/validate_token_qa_data.py --task ner-csv --input ner.csv
python scripts/validate_token_qa_data.py --task ner-conll --input ner.txt
python scripts/validate_token_qa_data.py --task qa-json --input train.json
python scripts/validate_token_qa_data.py --task qa-jsonl --input train.jsonl
python scripts/validate_token_qa_data.py --task qa-predict-json --input predict.json
```

The QA validator checks that non-impossible answer text matches the context at `answer_start`.
