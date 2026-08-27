# NLG GPT-2 troubleshooting

## Missing vocab or checkpoints

- `FileNotFoundError` for `vocab`, `init_checkpoint`, or `lora_path`: check the
  model card and directory layout before training or decoding. The repository's
  recipes assume a GPT-2 vocabulary directory and a separate base checkpoint.
- Keys do not load cleanly: verify that the same model card, rank, and alpha are
  used for training, beam search, and decoding. The GPT-2 model code normalizes
  some historical parameter suffixes, but it cannot reconcile a different model
  size or data layout.

## JSONL and formatting problems

- `validate_nlg_jsonl.py` reports a missing `context`, `completion`, or `predict`
  key: the file is at the wrong stage of the pipeline. Recreate the conversion
  or decode stage instead of trying to pass a training file into decoding.
- Empty prediction/reference counts or mismatched ids: ensure the sample reader
  and input reader traverse the same records in the same order. For WebNLG and
  DART, also check `--ref_num`.
- Unexpected metric output: confirm that `--tokenize` and `--lower` match the
  evaluator's expectations and that the reference files are written in the same
  normalization as the hypotheses.

## Training and generation

- `torch.distributed.launch` no longer exists in the local environment: use the
  launcher your installed PyTorch supports, but keep the arguments identical.
- Out-of-memory: lower batch size first. The archived recipes are large, and the
  command builder intentionally produces a reproducible but not resource-light
  command.
- The model appears to train everything: call `mark_only_lora_as_trainable`
  after building the GPT-2 model and before constructing the optimizer.

## External evaluation

E2E, WebNLG, and DART metric scripts are external projects. Missing Perl, Java,
NLTK data, or clone access should be treated as an environment limitation, not
as a LoRA code error. Validate the intermediate JSONL files and decoded text
first; only then troubleshoot the evaluator.
