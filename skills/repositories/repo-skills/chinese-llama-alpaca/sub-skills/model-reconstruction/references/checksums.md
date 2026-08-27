# Checksum Reference

The original project publishes SHA256 values for original LLaMA files, Chinese tokenizers, LoRA adapter weights, and selected merged outputs. Use these checks before merging or debugging corrupted downloads.

Use the root helper from the generated skill tree:

```bash
python ../../scripts/verify_sha256.py /path/to/adapter_model.bin \
  --expected adapter_model.bin=<expected-hex>
```

The helper also accepts basenames, so `--expected tokenizer.model=<hex>` works when the hashed path basename is `tokenizer.model`.

## Tokenizer Digests

| Model type | File | SHA256 |
| --- | --- | --- |
| LLaMA tokenizer for 7B/13B/33B variants | `tokenizer.model` | `e2676d4ca29ca1750f6ff203328d73b189321dc5776ceede037cbd36541d70c0` |
| Alpaca tokenizer for 7B/13B/33B variants | `tokenizer.model` | `2d967e855b1213a439df6c8ce2791f869c84b4f3b6cfacf22b86440b8192a2f8` |

## LoRA Adapter Weight Digests

Hash the `adapter_model.bin` inside the LoRA directory after extracting or downloading.

| LoRA model | SHA256 |
| --- | --- |
| Chinese-LLaMA-7B | `2a2c24d096f5d509f24946fdbd8c25e1ce4a0acb955902f7436d74c0c0379d86` |
| Chinese-LLaMA-Plus-7B | `8c928db86b2a0cf73f019832f921eb7e1e069ca21441b4bfa12c4381c6cc46be` |
| Chinese-LLaMA-13B | `6a4ce789d219bde122f8d9a20371937f2aa2ee86a2311d9f5e303df2e774f9fc` |
| Chinese-LLaMA-Plus-13B | `784fcff9c4bdf4e77d442a01158e121caf8fcce0f97ffb32396fe7a3617ee7e8` |
| Chinese-LLaMA-33B | `93a449bafb71ff1bb74a4a21e64e102e5078e5c3898eb40d013790072a0fa3de` |
| Chinese-LLaMA-Plus-33B | `16f2544f4b5be9840dbb1a8071a9bc42627ed4232be3b0b600b43f7b4b5f08a7` |
| Chinese-Alpaca-7B | `0d9b6ed8e4a7d1ae590a16c89a452a488d66ff07e45487972f61c2b6e46e36de` |
| Chinese-Alpaca-Plus-7B | `4ee0bf805c312a9a771624d481fbdb4485e1b0a70cd2a8da9f96137f177b795d` |
| Chinese-Alpaca-Pro-7B | `3cd2776908c3f5efe68bf6cf0248cb0e80fb7c55a52b8406325c9f0ca37b8594` |
| Chinese-Alpaca-13B | `cb8dda3c005f3343a0740dcd7237fbb600cb14b6bff9b6f3d488c086a2f08ada` |
| Chinese-Alpaca-Plus-13B | `a1fcdcb6d7e1068f925fb36ec78632c76058ba12ba352bed4d44060b8e6f4706` |
| Chinese-Alpaca-Pro-13B | `f076b20fc2390ddbc35fd56d580d46ea834b33bbae34a4bb3cb7b571e60602e0` |
| Chinese-Alpaca-33B | `6b39da4c682e715a9de30b247b7e9b812d2d54f7d320ec9b452000a5cd4d178d` |
| Chinese-Alpaca-Plus-33B | `411f5b9351abcc33c13a82bdd97ddcff81ad7993a8ddb83085b7ea97fad92fc7` |
| Chinese-Alpaca-Pro-33B | `0e7ba4951f605d2c0a7f0bcb983d7f6ed075c8dd23fbbcbc8a8c9643247212a3` |

## Original LLaMA Baseline Examples

The source project also lists digests for original LLaMA PTH and HF conversions. Check those when available, but remember the generated skill cannot provide or license those files. Common original PTH digests include:

| Original model | Shard | SHA256 |
| --- | --- | --- |
| LLaMA-7B | `consolidated.00.pth` | `700df0d3013b703a806d2ae7f1bfb8e59814e3d06ae78be0c66368a50059f33d` |
| LLaMA-13B | shard 0 | `745bf4e29a4dd6f411e72976d92b452da1b49168a4f41c951cfcc8051823cf08` |
| LLaMA-13B | shard 1 | `d5ccbcc465c71c0de439a5aeffebe8344c68a519bce70bc7f9f92654ee567085` |

For 33B/65B and merged-output digests, consult the user-provided release notes or verify against an archived copy of the original `SHA256.md`. Do not fabricate missing digest values.

## Interpreting Mismatches

- A mismatch before merge usually means a corrupted/incomplete download, wrong variant, or renamed file from another release.
- A merged-output mismatch can also come from PyTorch metadata differences. The original project says merged `consolidated.*.pth` checksums are most meaningful with PyTorch `>=1.13.0`.
- Tokenizer digest mismatch is a serious signal: stop and confirm LLaMA versus Alpaca tokenizer before merging.
