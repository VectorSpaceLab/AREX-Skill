# API Reference

## Core flow

`WordVocab` -> `BERTDataset` -> `DataLoader` -> `BERT` -> `BERTLM` -> `BERTTrainer`

## Public imports and signatures

| Symbol | Signature | What it does | Notes |
| --- | --- | --- | --- |
| `bert_pytorch.BERT` | `BERT(vocab_size, hidden=768, n_layers=12, attn_heads=12, dropout=0.1)` | BERT encoder built from embeddings and transformer blocks. | `hidden` must be divisible by `attn_heads`. |
| `bert_pytorch.model.BERTLM` | `BERTLM(bert: BERT, vocab_size)` | Adds next-sentence and masked-language-model heads. | Returns log-probabilities from `LogSoftmax`. |
| `bert_pytorch.dataset.WordVocab` | `WordVocab(texts, max_size=None, min_freq=1)` | Builds a token vocabulary from an iterable of corpus lines or token lists. | Special token indices are fixed: pad 0, unk 1, eos 2, sos 3, mask 4. |
| `WordVocab.to_seq` | `to_seq(sentence, seq_len=None, with_eos=False, with_sos=False, with_len=False)` | Converts a string or token list to token ids. | Pads or truncates to `seq_len`. |
| `WordVocab.from_seq` | `from_seq(seq, join=False, with_pad=False)` | Converts ids back to tokens. | `join=True` returns a single string. |
| `WordVocab.load_vocab` | `load_vocab(vocab_path: str) -> WordVocab` | Loads a pickled vocabulary. | Only load trusted files. |
| `WordVocab.save_vocab` | `save_vocab(vocab_path)` | Saves the vocabulary with `pickle`. | The file is a Python pickle, not a text vocab. |
| `bert_pytorch.dataset.BERTDataset` | `BERTDataset(corpus_path, vocab, seq_len, encoding='utf-8', corpus_lines=None, on_memory=True)` | Reads tab-separated sentence pairs and produces BERT training items. | `on_memory=False` needs explicit `corpus_lines`. |
| `bert_pytorch.trainer.BERTTrainer` | `BERTTrainer(bert: BERT, vocab_size: int, train_dataloader, test_dataloader=None, lr: float = 0.0001, betas=(0.9, 0.999), weight_decay: float = 0.01, warmup_steps=10000, with_cuda=True, cuda_devices=None, log_freq=10)` | Wraps the model, optimizer, loss, and train/test loops. | Chooses CUDA only when available and requested. |
| `bert_pytorch.__main__.train` | `train()` | Console entry point used by `bert`. | Reads `argparse` arguments from `sys.argv`. |
| `bert_pytorch.dataset.vocab.build` | `build()` | Console entry point used by `bert-vocab`. | Reads `argparse` arguments from `sys.argv`. |

## Dataset item shape

`BERTDataset.__getitem__` returns a dict of tensors with these keys:

- `bert_input`: token ids for the masked input sequence.
- `bert_label`: token ids for the masked-language-model targets; padding positions are `0`.
- `segment_label`: segment ids, with `1` for the first sentence and `2` for the second.
- `is_next`: next-sentence label, `1` for a true pair and `0` for a random pair.

## Trainer behavior

- `BERTTrainer.train(epoch)` and `BERTTrainer.test(epoch)` both delegate to the same internal iteration loop.
- `BERTTrainer.save(epoch, file_path)` saves the model object with `torch.save(self.bert.cpu(), output_path)` and then moves it back to the active device.
- The saved filename is `file_path + ".ep{epoch}"`; the argument is a prefix, not a complete checkpoint name.
- The training loop uses `nn.NLLLoss(ignore_index=0)`, so padding id `0` is ignored.

## When to inspect this file

Read this reference when you need exact constructor arguments, default values, output fields, or object relationships before writing a smoke script or troubleshooting a failing call.
