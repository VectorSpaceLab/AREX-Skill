# HuggingFace and PEFT integration

This reference covers the optional HuggingFace surface that affects inference export.

## Optional dependencies

Install the extra packages only when you need them:

- `mosaicml[nlp]` for HuggingFace model support
- `peft` when you use `peft_config`
- `onnx` and `onnxruntime` when you want ONNX export validation or runtime checks
- tokenizer backends such as `sentencepiece` when the chosen tokenizer needs them

If `transformers` is missing, `HuggingFaceModel` raises a conditional-import error.
If `peft_config` is provided but PEFT is unavailable, the constructor raises a conditional-import error for PEFT.

## HuggingFaceModel signature

```python
HuggingFaceModel(
    model,
    tokenizer=None,
    use_logits=False,
    metrics=None,
    eval_metrics=None,
    shift_labels=None,
    allow_embedding_resizing=False,
    peft_config=None,
    should_save_peft_only=True,
)
```

## Tokenizer and embedding rules

- If no tokenizer is passed, the checkpoint will not store tokenizer config.
- If a tokenizer is passed and its vocab is larger than the model vocab, the constructor raises an error unless `allow_embedding_resizing=True`.
- If `allow_embedding_resizing=True`, the model embeddings are resized automatically to the tokenizer size.
- If the tokenizer vocab is smaller than the model vocab, resizing is optional; the code logs an informational message because larger embedding tables are sometimes intentional.

Practical choices:

- use `model.resize_token_embeddings(len(tokenizer))` yourself when you want the resize to be explicit
- use `allow_embedding_resizing=True` when you want the wrapper to do it for you

## PEFT rules

- Only LoRA is supported.
- `peft_config.peft_type` and `task_type` are normalized to upper case internally.
- `should_save_peft_only=True` keeps state dict saving limited to adapter weights when PEFT is active.
- `LoadCheckpoint` temporarily disables `should_save_peft_only` while loading so the checkpoint loader can see full weights.

## Checkpoint metadata

Composer checkpoints for HuggingFace models store metadata for:

- model config
- tokenizer files, when a tokenizer was provided
- PEFT config, when PEFT is active

That metadata is used by helper methods that reconstruct a HuggingFace model or write pretrained-style files back out.

Useful helpers:

- `HuggingFaceModel.hf_from_composer_checkpoint(...)`
- `write_huggingface_pretrained_from_composer_checkpoint(...)`

### What the helpers write

- `config.json`
- tokenizer files
- `pytorch_model.bin` for a regular HuggingFace model
- `adapter_model.bin` when a PEFT adapter is active

## Export implications

A HuggingFace model can be exported with the same inference API as any other `nn.Module`, but the following details matter:

- export after the model is in eval mode
- make sure the tokenizer is consistent with the model embeddings before export
- use a real example batch when exporting ONNX
- if the model was altered by surgery functions during training, prefer export through the Composer export API rather than trying to reconstruct pretrained files directly

## Typical decision points

### Tokenizer vocab is larger than the model vocab

Choose one of these:

1. resize the embeddings manually before constructing `HuggingFaceModel`
2. pass `allow_embedding_resizing=True`

### PEFT is required

Use a LoRA-only PEFT config and keep `peft` installed in the environment.

### Only inference export is needed

You can still use `export_for_inference` directly on the wrapped HuggingFace model; the wrapper does not change the export API, but it does affect checkpoint metadata and tokenizer behavior.
