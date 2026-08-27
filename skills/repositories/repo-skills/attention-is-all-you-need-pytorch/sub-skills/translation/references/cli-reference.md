# Translation CLI Reference

This reference captures the runtime behavior of the repository's `translate.py`
so a future agent can run translation without reopening the source files.

## README test command

The documented non-BPE test flow is:

```bash
python translate.py -data_pkl m30k_deen_shr.pkl -model trained.chkpt -output prediction.txt
```

For CPU-only execution, add `-no_cuda`:

```bash
python translate.py -data_pkl m30k_deen_shr.pkl -model trained.chkpt -output prediction.txt -no_cuda
```

## CLI options

| Option | Required | Default | Meaning |
|---|---:|---|---|
| `-model` | yes | none | Path to a checkpoint saved by `train.py`. |
| `-data_pkl` | yes | none | Pickle containing test examples and torchtext vocab fields. |
| `-output` | no | `pred.txt` | Destination text file; one decoded prediction per test example. |
| `-beam_size` | no | `5` | Beam width used by `Translator`. Must not exceed target vocabulary size. |
| `-max_seq_len` | no | `100` | Maximum generated sequence length inside the beam-search buffer. |
| `-no_cuda` | no | false | Forces CPU. Without it, the CLI selects CUDA unconditionally. |

The script has commented TODO options for raw `-src`, `-vocab`, batch
translation, `-batch_size`, and `-n_best`; those interfaces are not active.

## Device behavior

`translate.py` sets:

```python
opt.cuda = not opt.no_cuda
device = torch.device('cuda' if opt.cuda else 'cpu')
```

It does not check `torch.cuda.is_available()`. On a host without a usable CUDA
runtime, pass `-no_cuda`. If CUDA is selected, the checkpoint is loaded with
`map_location='cuda'`, the model is moved to CUDA, the translator buffers are
moved to CUDA, and each source tensor is moved to CUDA.

## Checkpoint schema expected by `load_model`

Training saves checkpoints as:

```python
checkpoint = {'epoch': epoch_i, 'settings': opt, 'model': model.state_dict()}
```

Translation requires these top-level keys:

| Key | Required | Runtime use |
|---|---:|---|
| `settings` | yes | Namespace or object holding the model hyperparameters and vocab sizes. |
| `model` | yes | `state_dict` loaded into the reconstructed `Transformer`. |
| `epoch` | no for translation | Informational training epoch. |

`load_model(opt, device)` reads `checkpoint['settings']` and reconstructs
`Transformer` with this mapping:

| Setting attribute | Used as |
|---|---|
| `src_vocab_size` | `Transformer(n_src_vocab=...)` |
| `trg_vocab_size` | `Transformer(n_trg_vocab=...)` |
| `src_pad_idx` | source padding index |
| `trg_pad_idx` | target padding index |
| `proj_share_weight` | `trg_emb_prj_weight_sharing` |
| `embs_share_weight` | `emb_src_trg_weight_sharing` |
| `d_k`, `d_v` | attention key/value dimensions |
| `d_model` | model dimension |
| `d_word_vec` | embedding dimension |
| `d_inner_hid` | feed-forward hidden size (`d_inner`) |
| `n_layers` | encoder/decoder layer count |
| `n_head` | attention head count |
| `dropout` | dropout probability, though the model is put in eval mode by `Translator` |

Current `translate.py` does **not** pass `scale_emb_or_prj` from the checkpoint
settings into `Transformer`; `Transformer` therefore uses its default `prj` mode
at translation time. Checkpoints trained with a non-default `scale_emb_or_prj`
are semantically suspicious even if their state dict can load.

## Data pickle schema expected by `translate.py`

The non-BPE translation path expects a trusted pickle with this shape:

```python
data = {
    'vocab': {
        'src': SRC_FIELD,
        'trg': TRG_FIELD,
    },
    'test': TEST_EXAMPLES,
    # other keys such as settings/train/valid may also be present
}
```

Requirements used at runtime:

- `data['vocab']['src']` and `data['vocab']['trg']` are torchtext `Field`-like
  objects.
- Each field has a `.vocab.stoi` token-to-index mapping.
- The target field also has `.vocab.itos` for index-to-token decoding.
- Source OOV handling uses `SRC.unk_token` and
  `SRC.vocab.stoi[SRC.unk_token]`.
- The special token strings are fixed in the repository constants:
  - padding: `<blank>`
  - unknown: `<unk>`
  - beginning of target sentence: `<s>`
  - end of target sentence: `</s>`
- `data['test']` contains torchtext `Example`-like objects. Translation reads
  `example.src`; the repository constructs the `Dataset` with both `src` and
  `trg` fields, so examples that also carry `example.trg` are safest.

Use the bundled checkpoint inspector before long runs:

```bash
python scripts/inspect_checkpoint.py \
  --checkpoint trained.chkpt \
  --data-pkl m30k_deen_shr.pkl \
  --trust-inputs
```

Add `--repo-root /path/to/repo --instantiate-model` when you also want to prove
that a repository checkout can reconstruct the model and load the state dict on
CPU.

## Output semantics

For each example in `data['test']`, the CLI:

1. Maps each source token with `SRC.vocab.stoi.get(word, unk_idx)`.
2. Calls `translator.translate_sentence(torch.LongTensor([src_seq]).to(device))`.
3. Maps generated target indices through `TRG.vocab.itos`.
4. Joins target tokens with spaces.
5. Removes literal `<s>` and `</s>` substrings by `str.replace(...)`.
6. Writes the stripped line to the output file.

Consequences:

- One output line is produced per test example.
- Source OOV tokens are silently mapped to the source unknown index.
- The generated sequence can include padding or other target tokens if the model
  emits them; only BOS/EOS strings are stripped.
- BPE decoding is not implemented in this CLI. The README marks BPE testing as
  not ready and lists decoding after translation as TODO.
