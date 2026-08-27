# Token and QA Workflows

## NER CPU smoke recipe

```python
import pandas as pd
from simpletransformers.ner import NERModel

train_df = pd.DataFrame(
    [[0, "Simple", "B-MISC"], [0, "Transformers", "I-MISC"], [0, "works", "O"]],
    columns=["sentence_id", "words", "labels"],
)
args = {"no_save": True, "overwrite_output_dir": True, "reprocess_input_data": True, "num_train_epochs": 1}
model = NERModel("bert", "bert-base-uncased", args=args, use_cuda=False)
model.train_model(train_df)
result, outputs, predictions = model.eval_model(train_df)
predictions, raw_outputs = model.predict(["Simple Transformers works"])
```

This downloads the model unless cached. For pure schema checks, run the validator.

## NER custom tokenization

When token boundaries matter, pass manually tokenized lists and `split_on_space=False`:

```python
model.predict([["New", "York", "City"]], split_on_space=False)
```

Keep training `words` values aligned with the intended tokenization.

## QA CPU smoke recipe

```python
from simpletransformers.question_answering import QuestionAnsweringModel

train_data = [
    {
        "context": "This context contains the answer.",
        "qas": [{"id": "0", "question": "What contains the answer?", "is_impossible": False,
                 "answers": [{"text": "context", "answer_start": 5}]}],
    }
]
args = {"no_save": True, "overwrite_output_dir": True, "reprocess_input_data": True, "num_train_epochs": 1}
model = QuestionAnsweringModel("bert", "bert-base-uncased", args=args, use_cuda=False)
model.train_model(train_data)
model.eval_model(train_data)
model.predict([{"context": "A small prediction context.", "qas": [{"id": "p0", "question": "What is small?"}]}])
```

## QA span preparation

Compute `answer_start` from the exact context string rather than by hand:

```python
answer = "Brandon Sanderson"
context = "Mistborn was written by Brandon Sanderson."
answer_start = context.index(answer)
```

If `context.index(answer)` fails, the training row is invalid.

## Lazy loading

Use lazy loading only when memory is the bottleneck and the user accepts file-backed training. Validate each line as standalone JSON and keep evaluation in normal list/JSON form.

## When to run native tests

Repo-native NER and QA tests are valuable but train public Hugging Face checkpoints. Run them only with approved network/model-cache/compute budget; otherwise use schema validators plus source-backed recipes.
