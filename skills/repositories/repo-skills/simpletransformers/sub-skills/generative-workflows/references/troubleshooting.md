# Generative Workflow Troubleshooting

## T5 prediction missing prefix

Symptoms: prediction quality is nonsensical or preprocessing errors mention missing task prefix.

Recovery: make prediction strings look like `"task: input text"`. Training/eval DataFrames separate `prefix` from `input_text`; prediction lists do not.

## Seq2Seq constructor confusion

If using BART/Marian-style unified models, pass `encoder_decoder_type` and `encoder_decoder_name`. If using separate encoder/decoder models, pass `encoder_type`, `encoder_name`, and `decoder_name`. Mixing these forms leads to confusing tokenizer/config errors.

## Language modeling from scratch

When `model_name=None`, set `vocab_size` and provide `train_files`. ELECTRA from-scratch runs require compatible generator/discriminator configs. Without these, tokenizer/model construction fails before training.

## Unexpected downloads or long runs

Any constructor with a public model name can download checkpoints. Validate data first, use cached/tiny models for smoke runs, and ask before full training.

## ConvAI cached_path import errors

Simple Transformers 0.70.8 ConvAI utilities import `cached_path` from Transformers. Modern Transformers removed this top-level helper. Resolve package compatibility before debugging ConvAI data.

## SequenceSummary / TransfoXL import errors

Generation and shared custom model modules can fail under modern Transformers versions. Treat these as dependency-version problems; they are not fixed by changing task data.
