# Translation API Reference

This reference covers the programmatic API needed to load a trained Transformer
checkpoint and run beam search for one tokenized source sentence.

## Constants

The repository defines these token strings:

| Name | Value | Translation use |
|---|---|---|
| `PAD_WORD` | `<blank>` | Padding index for source/target masks and beam buffers. |
| `UNK_WORD` | `<unk>` | Conventional unknown token string. The CLI uses `SRC.unk_token` for the actual field. |
| `BOS_WORD` | `<s>` | Target beginning-of-sentence index used to seed beam search. |
| `EOS_WORD` | `</s>` | Target end-of-sentence index used to stop and length-normalize beams. |

## `Transformer` construction used by translation

Translation reconstructs the model from checkpoint settings with the public
signature:

```python
Transformer(
    n_src_vocab, n_trg_vocab, src_pad_idx, trg_pad_idx,
    d_word_vec=512, d_model=512, d_inner=2048,
    n_layers=6, n_head=8, d_k=64, d_v=64,
    dropout=0.1, n_position=200,
    trg_emb_prj_weight_sharing=True,
    emb_src_trg_weight_sharing=True,
    scale_emb_or_prj='prj',
)
```

`translate.py` passes every listed hyperparameter except `n_position` and
`scale_emb_or_prj`, so those two use current code defaults (`200` and `prj`).
If a checkpoint was trained after changing either behavior, validate carefully.

## `Translator` constructor

```python
Translator(
    model,
    beam_size,
    max_seq_len,
    src_pad_idx,
    trg_pad_idx,
    trg_bos_idx,
    trg_eos_idx,
)
```

Important behavior:

- It is a `torch.nn.Module` and registers beam buffers (`init_seq`,
  `blank_seqs`, `len_map`). Call `.to(device)` on the translator after
  construction so those buffers move with the model.
- It stores the model and immediately calls `self.model.eval()`.
- Beam-search length normalization uses `alpha = 0.7` after every beam has
  produced EOS.
- `beam_size` must be no larger than the target vocabulary size because the
  implementation calls `topk(beam_size)` on target probabilities.
- `max_seq_len` should be at least 3. Very small values can leave internal loop
  variables unset in the original implementation.

## `translate_sentence(src_seq)`

Input contract:

```python
src_seq.dtype == torch.long
src_seq.shape == (1, source_length)
src_seq.device == translator buffers/model device
```

The method asserts batch size one:

```python
assert src_seq.size(0) == 1
```

It returns a Python `list[int]` of target vocabulary indices. The first element
is seeded with the target BOS index. If EOS is found, the returned list includes
EOS; otherwise it can run to `max_seq_len`. The CLI converts indices to target
strings and removes literal BOS/EOS strings afterward.

## Minimal programmatic pattern

```python
import torch
import dill as pickle
import transformer.Constants as Constants
from transformer.Models import Transformer
from transformer.Translator import Translator

checkpoint = torch.load('trained.chkpt', map_location='cpu')
settings = checkpoint['settings']

data = pickle.load(open('m30k_deen_shr.pkl', 'rb'))
SRC = data['vocab']['src']
TRG = data['vocab']['trg']

src_pad_idx = SRC.vocab.stoi[Constants.PAD_WORD]
trg_pad_idx = TRG.vocab.stoi[Constants.PAD_WORD]
trg_bos_idx = TRG.vocab.stoi[Constants.BOS_WORD]
trg_eos_idx = TRG.vocab.stoi[Constants.EOS_WORD]

model = Transformer(
    settings.src_vocab_size,
    settings.trg_vocab_size,
    src_pad_idx,
    trg_pad_idx,
    trg_emb_prj_weight_sharing=settings.proj_share_weight,
    emb_src_trg_weight_sharing=settings.embs_share_weight,
    d_k=settings.d_k,
    d_v=settings.d_v,
    d_model=settings.d_model,
    d_word_vec=settings.d_word_vec,
    d_inner=settings.d_inner_hid,
    n_layers=settings.n_layers,
    n_head=settings.n_head,
    dropout=settings.dropout,
)
model.load_state_dict(checkpoint['model'])

device = torch.device('cpu')
translator = Translator(
    model=model.to(device),
    beam_size=5,
    max_seq_len=100,
    src_pad_idx=src_pad_idx,
    trg_pad_idx=trg_pad_idx,
    trg_bos_idx=trg_bos_idx,
    trg_eos_idx=trg_eos_idx,
).to(device)

unk_idx = SRC.vocab.stoi[SRC.unk_token]
src_tokens = ['ein', 'mann', 'geht']
src_ids = [SRC.vocab.stoi.get(tok, unk_idx) for tok in src_tokens]
pred_ids = translator.translate_sentence(torch.LongTensor([src_ids]).to(device))
pred_tokens = [TRG.vocab.itos[i] for i in pred_ids]
pred_line = ' '.join(pred_tokens).replace(Constants.BOS_WORD, '').replace(Constants.EOS_WORD, '').strip()
```

For a quick API-only sanity check that does not need a checkpoint, run:

```bash
python scripts/translation_smoke_check.py --repo-root /path/to/repo --device cpu
```
