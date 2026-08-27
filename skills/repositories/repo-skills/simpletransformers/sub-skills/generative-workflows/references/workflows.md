# Generative Workflows

## Language modeling fine-tuning

```python
from simpletransformers.language_modeling import LanguageModelingModel

args = {"no_save": True, "overwrite_output_dir": True, "reprocess_input_data": True, "num_train_epochs": 1}
model = LanguageModelingModel("bert", "bert-base-uncased", args=args, train_files="train.txt", use_cuda=False)
model.train_model("train.txt")
```

For from-scratch models, pass `model_name=None` and set `vocab_size`; ELECTRA also needs generator/discriminator config dictionaries.

## Language generation

```python
from simpletransformers.language_generation import LanguageGenerationModel
model = LanguageGenerationModel("gpt2", "gpt2", args={"max_length": 50}, use_cuda=False)
outputs = model.generate("Once upon a time", verbose=False)
```

Set sampling parameters deliberately. Do not leave unconstrained generation in unattended workflows.

## T5 text-to-text

```python
from simpletransformers.t5 import T5Model
model = T5Model("t5", "t5-small", args={"num_train_epochs": 1, "max_length": 32}, use_cuda=False)
model.train_model(train_df)  # prefix, input_text, target_text
model.predict(["summarize: short source text"])
```

Prediction strings must include the `prefix: ` separator even when `preprocess_inputs=True`.

## Seq2Seq constructor choice

Unified encoder-decoder model:

```python
model = Seq2SeqModel(encoder_decoder_type="bart", encoder_decoder_name="facebook/bart-base", use_cuda=False)
```

Separate encoder and decoder:

```python
model = Seq2SeqModel(encoder_type="roberta", encoder_name="roberta-base", decoder_name="bert-base-cased", use_cuda=False)
```

Use the second form only when the architecture actually supports separate encoder/decoder composition.

## ConvAI

ConvAI exposes `interact()` and `interact_single()`. Avoid these in non-interactive automation unless the user explicitly wants a chatbot loop. Validate import compatibility before preparing conversation datasets.

## Scale-up policy

1. Validate input files.
2. Run a CPU/no-save smoke path when a cached tiny model is available.
3. Only then expand epochs, checkpoint saving, mixed precision, GPU, WandB, and generated-text metrics.
