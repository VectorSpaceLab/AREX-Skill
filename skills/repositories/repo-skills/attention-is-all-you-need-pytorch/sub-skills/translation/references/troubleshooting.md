# Translation Troubleshooting

## Fast diagnostic order

1. Run `scripts/inspect_checkpoint.py --checkpoint ... --data-pkl ... --trust-inputs`.
2. If checkpoint loading itself is suspect, rerun with `--repo-root . --instantiate-model`.
3. If the API path is suspect independent of your checkpoint, run
   `scripts/translation_smoke_check.py --repo-root . --device cpu`.
4. Only then launch the full `translate.py` job.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `KeyError: 'settings'` or `KeyError: 'model'` | The file is not a `train.py` checkpoint or was saved in a different format. | Use a checkpoint saved as `{'epoch', 'settings', 'model'}` or convert it before translation. |
| `AttributeError` on settings such as `src_vocab_size` or `d_inner_hid` | The settings object was not produced by the expected training CLI or was edited. | Inspect settings, add missing attributes only if you know the original architecture, then retry. |
| `RuntimeError: Error(s) in loading state_dict` | Hyperparameters/vocab sizes/sharing flags do not match the state dict. | Validate the checkpoint settings, data-pickle vocab sizes, and whether `proj_share_weight` / `embs_share_weight` match training. |
| Translation quality is unexpectedly bad despite loading | `translate.py` always uses `scale_emb_or_prj='prj'` and `n_position=200` defaults. | Treat checkpoints trained with non-default scaling/position behavior as incompatible with the unmodified CLI unless you adapt loading code. |
| `AssertionError` in `translate_sentence` | Source tensor batch size is not one. | Pass a tensor shaped `(1, src_len)` and loop over examples manually. |
| CUDA error on CPU-only machine | CLI selected CUDA because `-no_cuda` was omitted. | Add `-no_cuda` for the CLI, or use `device=torch.device('cpu')` in API code. |
| Device mismatch between tensors and model | Model/translator buffers are on one device while `src_seq` is on another. | Move model, translator, and source tensor to the same device; call `.to(device)` on the translator. |
| `topk` out-of-range error | `beam_size` exceeds target vocabulary size. | Lower `-beam_size` or use a checkpoint/data pickle with the expected target vocab. |
| Index error while mapping `TRG.vocab.itos[idx]` | Model output vocabulary and target field vocabulary do not match. | Check `settings.trg_vocab_size == len(TRG.vocab)` and use the data pickle paired with the checkpoint. |
| Source words become `<unk>` silently | CLI maps missing source tokens with `SRC.vocab.stoi.get(word, unk_idx)`. | Ensure tokenization/casing matches preprocessing, or inspect OOV rate before translating. |
| Pickle load fails with torchtext/spaCy/dill errors | The runtime lacks compatible dependencies for the serialized `Field`/examples. | Use the verified package environment family for this repo; the known compatible stack includes torchtext 0.6.x and dill 0.3.x. |
| BPE output still contains subword marks | The repository marks BPE translation decoding as TODO/not ready. | Do not claim BPE post-processing is supported by the stock translation CLI; add a separate verified decoder if needed. |

## Checkpoint/data pairing checklist

- `checkpoint['settings'].src_vocab_size == len(data['vocab']['src'].vocab)`.
- `checkpoint['settings'].trg_vocab_size == len(data['vocab']['trg'].vocab)`.
- Source and target pad indices in settings match the indices of `<blank>` in
  the data pickle.
- Target BOS/EOS tokens `<s>` and `</s>` exist in `TRG.vocab.stoi`.
- If `settings.embs_share_weight` is true, source and target vocab mappings
  should be identical or intentionally shared.
- If the checkpoint came from a modified training script, verify any new model
  constructor options are also supplied during translation.

## Security note for pickles

Both PyTorch checkpoints containing Python settings objects and dill data
pickles can execute arbitrary pickle payloads when loaded. The bundled inspector
therefore requires `--trust-inputs` before loading them. Only inspect files from
trusted training/preprocessing runs.
