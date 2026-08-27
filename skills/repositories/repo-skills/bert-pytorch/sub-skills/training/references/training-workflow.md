# Training Workflow

## Typical flow

1. Build or load a vocab from a tab-separated corpus.
2. Create a `BERTDataset` and wrap it in a `DataLoader`.
3. Instantiate `BERT(vocab_size, hidden, n_layers, attn_heads)`.
4. Wrap the model in `BERTTrainer`.
5. Run `trainer.train(epoch)` and then `trainer.save(epoch, output_prefix)`.

## Device selection

`BERTTrainer` chooses its device like this:

- If CUDA is available and `with_cuda=True`, it uses `cuda:0`.
- If multiple GPUs are visible and `with_cuda=True`, it wraps the model in `nn.DataParallel`.
- Otherwise it uses CPU.

Use `scripts/train_smoke.py --device cpu` when you want to force a CPU run even on a GPU host.

## Key trainer behavior

- `BERTTrainer.train(epoch)` and `BERTTrainer.test(epoch)` share the same iteration loop.
- The training loop computes two losses: next-sentence prediction and masked-language-model prediction.
- Padding tokens with id `0` are ignored by the loss function.
- `BERTTrainer.save(epoch, file_path)` saves the underlying BERT model object, not a `state_dict`.
- The saved file name is `file_path + ".ep{epoch}"`.

## Parameter constraints

- `hidden` must be divisible by `attn_heads`.
- `batch_size`, `seq_len`, `hidden`, and `layers` all affect memory use.
- Small smoke runs work best with tiny values such as `hidden=32`, `layers=2`, `attn_heads=4`, `batch_size=2`, and `seq_len=8`.

## Tiny smoke recipe

```bash
python scripts/make_tiny_corpus.py --output /tmp/bert-pytorch-corpus.txt
python sub-skills/training/scripts/train_smoke.py --device cpu --epochs 1 --workdir /tmp/bert-pytorch-smoke
```

The bundled training helper uses a deterministic smoke dataset wrapper that guarantees masked tokens, so the loss stays finite on tiny corpora.

## When to inspect this file

Read this reference when you need the exact model/trainer flow, device behavior, checkpoint semantics, or the safe parameter choices for a tiny smoke run.
