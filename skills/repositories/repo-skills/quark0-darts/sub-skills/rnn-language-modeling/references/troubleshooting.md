# RNN Troubleshooting

Use this reference when a recurrent DARTS PTB/WT2 workflow fails before producing usable validation or test perplexity.

## Fast diagnosis matrix

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `AssertionError` during corpus loading | `Corpus.tokenize()` asserts that `train.txt`, `valid.txt`, or `test.txt` exists. | Confirm `--data` points to the directory containing all three exact filenames, not to one text file. Even `test.py` constructs all three splits before evaluating test data. |
| Empty or tiny batches | Corpus files are too small for the chosen `batch_size`, or many tokens were trimmed by `batchify()`. | Check token counts after whitespace splitting plus `<eos>`; reduce `batch_size` for small smoke data. |
| User passed `--cuda` but CUDA turned off | The flag is inverted: parsers use `action='store_false'`, so CUDA is enabled by default and passing `--cuda` disables it. | For faithful script behavior, do not pass `--cuda`; set `--gpu` for the device id. If intentionally disabling CUDA, warn that the RNN scripts still have CPU caveats. |
| CPU-only search fails | Search allocates architecture weights with `.cuda()` and unrolled search constructs cloned models with `.cuda()`. | Treat RNN architecture search as accelerator-required unless the code is ported. A CPU-only run is not a supported original path. |
| CPU-only train/test fails after loading a model | `train.py` and `test.py` call `model.cuda()` for loaded/best models even if CUDA was disabled earlier. | Use a compatible CUDA runtime or patch the script consistently for CPU; do not present `--cuda` as a reliable CPU fallback. |
| `AssertionError` from model construction | `RNNModel` asserts `ninp == nhid == nhidlast`. | Set `--emsize`, `--nhid`, and `--nhidlast` to the same value. The WT2 README recipe sets all three to `700`; PTB train defaults set all three to `850`; search defaults set all three to `300`. |
| `batch_size must be divisible by small_batch_size` | The micro-batch size does not divide the full batch size. | Leave `--small_batch_size` unset to default it to `--batch_size`, or choose a divisor such as `--batch_size 64 --small_batch_size 16`. |
| `torch.load()` returns the wrong object shape/type | `test.py` and resume paths expect a full serialized model object, not a state dictionary. | Use a `model.pt` produced by `save_checkpoint()` or an equivalent full-module file. For `--continue_train`, keep `model.pt`, `optimizer.pt`, and `misc.pt` together in the `--save` directory. |
| Repeated `rolling back to the previous best model ...` | `train.py` caught an exception; the explicit NaN check is one trigger. | Inspect the preceding batch logs. If it is numerical instability, lower `--lr`, reduce `--batch_size` or `--small_batch_size`, reduce hidden sizes, or shorten BPTT. If it is a data/checkpoint error, fix that root cause before resuming. |
| Out-of-memory during train/search | Large `batch_size`, `small_batch_size`, hidden dimensions, `bptt`, or sampled sequence length exceeded memory. | Reduce `--small_batch_size` first while keeping it a divisor of `--batch_size`; otherwise reduce `--batch_size`, `--emsize`/`--nhid`/`--nhidlast`, `--bptt`, or `--max_seq_len_delta`. |
| Search appears promising but final model is poor | Search validation perplexity is only a proxy and different seeds can find different local minima. | Repeat search with different seeds when budget allows, then retrain candidate genotypes from scratch and compare validation/test perplexity from `train.py`. |
| Custom `--arch` fails | The training script looks up the architecture name from the genotype catalog. | Use an existing genotype symbol or add a valid recurrent genotype before invoking `train.py --arch NAME`; route catalog/schema work to the genotype/visualization sub-skill. |

## Dataset-specific checks

1. Confirm layout:

   ```text
   <corpus-root>/train.txt
   <corpus-root>/valid.txt
   <corpus-root>/test.txt
   ```

2. Confirm the command uses `--data <corpus-root>`.
3. Remember every line gets a trailing `<eos>` token. Blank lines are not ignored by `Corpus`; they become an `<eos>` token.
4. For smoke data, make each split long enough for at least one batch at the planned batch size. `batchify()` discards the remainder after `floor(num_tokens / batch_size) * batch_size`.
5. If the vocabulary seems unexpectedly large, check for tokenization mismatches: no normalization or OOV handling is applied, and validation/test-only tokens extend the same dictionary.

## CUDA and CPU caveats

The recurrent scripts default to CUDA but express this backwards in the CLI:

- `--cuda` means "set `args.cuda` to false".
- With a GPU present and `args.cuda` false, the scripts print a warning telling the user they probably should run with CUDA.
- Some RNN code paths ignore a CPU intent and still call `.cuda()` or construct CUDA tensors.

Therefore, for faithful PTB/WT2 search/training/evaluation, plan on a compatible CUDA-capable runtime. If a user requests CPU-only behavior, frame it as a code-porting/debugging task rather than a native DARTS workflow.

## Checkpoint loading and resume

Normal checkpoints contain:

- `model.pt`: full serialized model object.
- `optimizer.pt`: serialized optimizer state.
- `misc.pt`: dictionary with the next epoch number.

`--continue_train` loads `model.pt`, reconstructs SGD or ASGD depending on whether the optimizer state contains `t0`, loads `optimizer.pt`, and resumes from `misc.pt` when rollback happens. Keep these files from the same run together. Mixing a model from one run with another optimizer state can break ASGD averaging or hidden-size assumptions.

`test.py --model_path PATH` only needs the model file, but that file must deserialize to a model object with parameters and `.cuda()` support. A bare state dictionary or incompatible class definition will not work without adapting the loader.

## NaN rollback and numerical instability

`train.py` checks `np.isnan(total_loss[0])` inside the training loop and raises when the accumulated loss becomes NaN. The broad exception handler then reloads the previous checkpoint and continues. This is useful for transient instability, but repeated rollback means the run is not progressing.

Stabilization levers, from least invasive to most invasive:

1. Ensure the dataset and checkpoint are correct; data errors can be hidden by the broad rollback handler.
2. Lower `--lr` from the default `20`.
3. Reduce `--small_batch_size` to fit memory while preserving the full `--batch_size` gradient accumulation plan.
4. Reduce `--batch_size` if memory or instability persists.
5. Reduce `--bptt` or `--max_seq_len_delta` to shorten sequences.
6. Use smaller but equal `--emsize`, `--nhid`, and `--nhidlast` for smoke/debug runs.
7. Revisit dropout and regularization flags only after the above checks.

## Memory and micro-batch guidance

`small_batch_size` is a micro-batch size for accumulating gradients until the full `batch_size` is reached. The scripts create one hidden state per micro-batch slot:

```text
num_micro_batches = batch_size // small_batch_size
hidden[i] shape = [1, small_batch_size, nhid]
```

Use this when a full batch does not fit in memory. Keep `batch_size` for the effective optimization batch and lower `small_batch_size` to the largest divisor that fits. If even `small_batch_size=1` does not fit, reduce hidden/embedding dimensions or sequence length.
