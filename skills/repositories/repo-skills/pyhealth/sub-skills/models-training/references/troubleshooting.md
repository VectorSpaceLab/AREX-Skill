# Model-training troubleshooting

- **`unexpected keyword argument`/missing key:** compare `batch.keys()` with
  the selected model forward signature and task `input_schema`; repair the task
  or processor contract before changing the model.
- **Embedding index out of range:** token IDs exceed the fitted processor/model
  vocabulary. Refit on training data, preserve PAD/UNK policy, and check code
  mapping; do not increase embedding size without recording the change.
- **Shape mismatch:** inspect processor `schema()`/`dim()` and one sample before
  collation. Image/signal/time/text outputs often have different spatial/time
  axes.
- **`loss` absent:** the model may be inference-only, in the wrong mode, or
  receiving the wrong label field. `Trainer.train` requires a forward result
  containing `loss`.
- **No metric/best checkpoint:** ensure `model.mode`, validation loader,
  `monitor`, and metric name agree. A checkpoint file alone is not evidence of
  model quality.
- **CUDA error/OOM:** verify the PyTorch CUDA build and device, then reduce
  batch/sequence size or use an explicit CPU smoke. Do not call CPU execution a
  CUDA validation.
- **Checkpoint mismatch:** load the same class/config and use
  `torch.load(..., map_location=device, weights_only=True)` semantics through
  `Trainer.load_ckpt`; compare state-dict keys and package version.
- **External-weight failure:** test local tokenization/architecture first;
  network, credentials, cache corruption, revision mismatch, and VRAM are
  separate failure classes.
