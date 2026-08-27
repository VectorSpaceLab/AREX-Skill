# DARTS RNN Workflows

This reference distills the recurrent DARTS language-modeling workflows for Penn Treebank (PTB) and WikiText-2 (WT2). It is command-planning guidance; the scripts are long-running, dataset-dependent, and assume the DARTS legacy runtime handled by the root skill.

## Workflow map

| Workflow | Canonical command | Main output | Expected signals |
| --- | --- | --- | --- |
| PTB architecture search | `cd rnn && python train_search.py --unrolled` | `search-EXP-<timestamp>/` unless `--save` changes the prefix | Logs parameter size, initial genotype, periodic genotype and architecture-weight softmax, validation loss/perplexity, and `Saving Normal!` when validation improves. |
| PTB train/evaluate | `cd rnn && python train.py` | `eval-EXP-<timestamp>/` unless `--save` changes the prefix | Logs train loss/perplexity during batches, end-of-epoch validation loss/perplexity, `Saving Normal!` or `Saving Averaged!`, then final test loss/perplexity. |
| PTB pretrained test | `cd rnn && python test.py --model_path ptb_model.pt` | stdout only | Loads a full serialized model object and prints final test loss/perplexity. README evidence reports 55.68 test perplexity with 23M parameters for the supplied PTB model. |
| WT2 train/evaluate | `cd rnn && python train.py --data ../data/wikitext-2 --dropouth 0.15 --emsize 700 --nhidlast 700 --nhid 700 --wdecay 5e-7` | `eval-EXP-<timestamp>/` unless `--save` changes the prefix | Same train/evaluate signals as PTB. The README recipe overrides data, hidden/embedding size, hidden dropout, and weight decay; it does not provide a pinned WT2 perplexity target. |

Search validation performance is not the final architecture quality signal. Use search to derive a recurrent genotype, then train the selected genotype from scratch with the full training workflow and judge validation/test perplexity there.

## PTB architecture search

Use search when the user needs a recurrent cell discovered on PTB.

Key defaults in `train_search.py`:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--data` | `../data/penn/` | Directory containing `train.txt`, `valid.txt`, and `test.txt`. |
| `--emsize`, `--nhid`, `--nhidlast` | `300`, `300`, `300` | Search proxy embedding and hidden sizes; all must stay equal because the model asserts equality. |
| `--epochs` | `50` | Search epoch count. |
| `--batch_size` | `256` | Token-stream batch size. |
| `--small_batch_size` | `-1` -> `batch_size` | Micro-batch size for gradient accumulation; must divide `batch_size`. |
| `--bptt` | `35` | Sequence length for truncated BPTT. |
| `--lr`, `--clip`, `--wdecay` | `20`, `0.25`, `5e-7` | Network optimizer learning rate, gradient clipping, and weight decay. |
| `--dropout`, `--dropouth`, `--dropoutx`, `--dropouti`, `--dropoute` | `0.75`, `0.25`, `0.75`, `0.2`, `0` | Output, hidden-state, cell-input, embedding, and embedded-word dropout controls. |
| `--arch_lr`, `--arch_wdecay` | `3e-3`, `1e-3` | Adam optimizer settings for architecture parameters. |
| `--unrolled` | off unless passed | Enables the one-step unrolled validation-loss architecture update used by the README command. |
| `--seed`, `--gpu` | `3`, `0` | RNG seed and GPU id. |

Search uses `Corpus(args.data)` and four token streams: train data for network weights, validation data batched as `search_data` for architecture updates, validation data at batch size 10 for evaluation, and test data at batch size 1. Each epoch calls `train()`, evaluates validation loss, and saves a checkpoint only when validation improves. There is no final test-set pass in the search script.

## PTB train and test

Use training when the user wants to evaluate a selected recurrent genotype from scratch on PTB.

Key defaults in `train.py`:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--data` | `../data/penn/` | PTB corpus directory. |
| `--arch` | `DARTS` | Genotype symbol to evaluate. Custom names must exist in the genotype catalog. |
| `--emsize`, `--nhid`, `--nhidlast` | `850`, `850`, `850` | Full-size embedding/hidden dimensions; all must be equal. |
| `--epochs` | `8000` | Upper training limit; early manual interruption is expected in practice. |
| `--batch_size` | `64` | Token-stream batch size. |
| `--small_batch_size` | `-1` -> `batch_size` | Micro-batch size for gradient accumulation; must divide `batch_size`. |
| `--bptt`, `--max_seq_len_delta` | `35`, `20` | Base sequence length and cap for random sequence-length variation. |
| `--lr`, `--clip`, `--wdecay` | `20`, `0.25`, `8e-7` | SGD/ASGD learning rate, gradient clipping, and weight decay. |
| `--dropout`, `--dropouth`, `--dropoutx`, `--dropouti`, `--dropoute` | `0.75`, `0.25`, `0.75`, `0.2`, `0.1` | Output, hidden-state, cell-input, embedding, and embedded-word dropout controls. |
| `--alpha`, `--beta` | `0`, `1e-3` | Activation and temporal activation regularization weights. |
| `--nonmono` | `5` | Non-monotonic validation window before switching from SGD to ASGD. |
| `--continue_train` | off unless passed | Resume from `model.pt`, `optimizer.pt`, and `misc.pt` in `--save`. |

The train script creates `eval-<save>-<timestamp>/` when not resuming, copies scripts into its `scripts/` subdirectory, trains with SGD first, validates every epoch, and finally reloads the best `model.pt` for test-set evaluation. Use `--arch <NAME>` only for a genotype symbol already available to the runtime; otherwise genotype lookup fails before model construction.

Use `test.py` only when the user already has a compatible serialized model file. `test.py` does not build a model from `--arch`; it calls `torch.load(args.model_path)` and expects a full module object, not just a state dictionary. It uses `Corpus(args.data)`, batchifies only the test split with batch size 1, and reports test perplexity.

## WT2 recipe

The WT2 README recipe is a training recipe, not a separate code path:

```bash
cd rnn && python train.py --data ../data/wikitext-2 \
  --dropouth 0.15 --emsize 700 --nhidlast 700 --nhid 700 --wdecay 5e-7
```

Keep the hidden-size equality invariant: if adapting the WT2 size, change `--emsize`, `--nhid`, and `--nhidlast` together. All other behavior, including checkpointing, ASGD switching, rollback, and final test evaluation, follows `train.py`.

## Checkpoints, ASGD, and rollback

- `create_exp_dir()` creates the experiment directory and copies current scripts into `scripts/` for provenance.
- `save_checkpoint(model, optimizer, epoch, path)` writes `model.pt`, `optimizer.pt`, and `misc.pt`; `misc.pt` stores the next epoch as `{'epoch': epoch + 1}`.
- `train_search.py` uses SGD for network weights plus Adam for architecture weights and saves `model.pt` when validation loss improves.
- `train.py` starts with SGD. If validation becomes non-monotonic for more than `--nonmono` history entries, it logs `Switching!` and replaces SGD with ASGD using `t0=0` and `lambd=0.`.
- When ASGD is active, validation temporarily swaps each parameter to the optimizer's averaged `ax` value. If validation improves, the script saves that averaged model and logs `Saving Averaged!`, then restores the live parameters.
- When normal SGD validation improves, the script logs `Saving Normal!` and writes a checkpoint.
- If training raises an exception, including the explicit NaN check in `train.py`, the script logs `rolling back to the previous best model ...`, reloads `model.pt` and `optimizer.pt`, restores the saved epoch from `misc.pt`, and continues.

## Perplexity interpretation

The scripts log negative log-likelihood loss and report perplexity as `exp(loss)`. Lower perplexity is better. For search, validation perplexity is a proxy for architecture optimization progress but should not be reported as the final model result. For training and testing, use validation perplexity to select/checkpoint the model and test perplexity as the final evaluation signal.
