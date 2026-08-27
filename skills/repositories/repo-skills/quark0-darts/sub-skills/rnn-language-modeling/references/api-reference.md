# RNN API Reference

This reference summarizes the recurrent language-modeling APIs that matter for planning, debugging, and explaining DARTS RNN workflows. It is not an import contract; the runtime is the script workflow described in [workflows.md](workflows.md).

## Data APIs

### `Dictionary`

- Fields: `word2idx`, `idx2word`, `counter`, and `total`.
- `add_word(word)` inserts the word if unseen, returns its integer id, increments `counter[token_id]`, and increments `total`.
- `len(dictionary)` returns the vocabulary size.

### `Corpus`

- Constructor: `Corpus(path)`.
- Builds one shared `Dictionary`.
- Tokenizes `train.txt`, `valid.txt`, and `test.txt` from the given directory.
- Returns flat `LongTensor` token streams as `corpus.train`, `corpus.valid`, and `corpus.test`.
- File existence is enforced with `assert os.path.exists(path)` inside `tokenize()`.

### `SentCorpus` and `BatchSentLoader`

- `SentCorpus(path)` uses the same dictionary and line tokenization but returns sentence tensors instead of flat streams.
- `BatchSentLoader(sents, batch_size, pad_id=0, cuda=False, volatile=False)` sorts sentence tensors by length and yields padded tensors shaped `[max_len, batch]`.
- These helpers are present in the data module but are not used by the README PTB/WT2 train, search, or test scripts.

## Model APIs

### `DARTSCell`

Constructor:

```python
DARTSCell(ninp, nhid, dropouth, dropoutx, genotype)
```

Key behavior:

- Uses `genotype.recurrent` to select one operation/predecessor edge per recurrent step.
- Uses `genotype.concat` to average selected intermediate states into the output hidden state.
- `forward(inputs, hidden)` expects embedded inputs shaped `[T, B, ninp]` and a one-layer hidden state in a list-like structure; it returns all hidden outputs across time plus the final hidden state.
- In training mode, input and hidden-state masks are generated with `mask2d()` and reused through the time loop.
- `_compute_init_state()` gates a candidate initial state from the current input and previous hidden state.
- Supported activation names inside the cell are `tanh`, `relu`, `sigmoid`, and `identity`; unknown names raise `NotImplementedError`.

Genotype catalog details and DOT rendering are owned by the genotype/visualization sub-skill. For API reasoning here, a recurrent genotype is a `Genotype(recurrent=[(op, pred), ...], concat=...)` object consumed by `DARTSCell`.

### `RNNModel`

Constructor:

```python
RNNModel(
    ntoken, ninp, nhid, nhidlast,
    dropout=0.5, dropouth=0.5, dropoutx=0.5,
    dropouti=0.5, dropoute=0.1,
    cell_cls=DARTSCell, genotype=None,
)
```

Key behavior:

- Asserts `ninp == nhid == nhidlast`. Tune `--emsize`, `--nhid`, and `--nhidlast` together.
- Creates an encoder embedding, one recurrent cell, and a decoder linear layer.
- Ties `decoder.weight` to `encoder.weight`.
- `init_hidden(bsz)` returns a one-element list containing zeros shaped `[1, bsz, nhid]` on the same tensor type as model parameters.
- `forward(input, hidden, return_h=False)` embeds token ids with `embedded_dropout()`, applies locked dropout to embeddings and outputs, runs the recurrent cell, decodes to vocabulary logits, and returns log-probabilities shaped `[T, B, ntoken]` plus the updated hidden state.
- With `return_h=True`, returns `(model_output, hidden, raw_outputs, outputs)`. The training loop uses `raw_outputs` and `outputs` for activation regularization (`alpha`) and temporal activation regularization (`beta`).
- If `cell_cls == DARTSCell`, a concrete genotype is required. Search uses a different cell class and requires `genotype is None`.

## Search model APIs

### `DARTSCellSearch`

- Subclasses `DARTSCell` with `genotype=None`.
- Adds `BatchNorm1d(nhid, affine=False)` on states.
- Computes `probs = softmax(weights, dim=-1)` over architecture weights.
- For each recurrent step, mixes candidate operations across predecessor states, skips the `none` primitive, and appends the weighted state.
- Averages the last `CONCAT` states as the output.

### `RNNModelSearch`

- Subclasses `RNNModel` using `DARTSCellSearch`.
- Saves constructor args for `new()` so unrolled optimization can construct a clone.
- `_initialize_arch_parameters()` creates small random architecture weights for every possible recurrent edge and shares the same `weights` variable across recurrent cells.
- `arch_parameters()` returns `[self.weights]` for the architecture optimizer.
- `_loss(hidden, input, target)` runs a forward pass and returns negative log-likelihood loss plus the next hidden state.
- `genotype()` parses softmax architecture weights by choosing, for each recurrent step, the predecessor/operation with the best non-`none` probability; it returns `Genotype(recurrent=gene, concat=range(STEPS+1)[-CONCAT:])`.

Search cells use the primitives `none`, `tanh`, `relu`, `sigmoid`, and `identity` and eight recurrent steps in the source design.

## Architecture optimizer API

### `Architect`

Constructor:

```python
Architect(model, args)
```

Key behavior:

- Stores network weight decay and gradient-clip settings from `args.wdecay` and `args.clip`.
- Creates `torch.optim.Adam(model.arch_parameters(), lr=args.arch_lr, weight_decay=args.arch_wdecay)`.
- `step(hidden_train, input_train, target_train, hidden_valid, input_valid, target_valid, network_optimizer, unrolled)` updates architecture parameters from validation loss.
- With `unrolled=False`, `_backward_step()` backpropagates validation loss directly.
- With `unrolled=True`, `_backward_step_unrolled()` builds an unrolled model after one network-weight update, computes validation gradients, applies a Hessian-vector product correction, and copies gradients back to the live architecture parameters.
- `_compute_unrolled_model()` uses the network optimizer's current learning rate as `eta`, clips network gradients, and constructs a cloned model from flattened parameters.
- `_hessian_vector_product()` finite-differences architecture gradients around the network-gradient vector.

## Utility APIs

### Batching and hidden-state helpers

- `batchify(data, bsz, args)` trims and reshapes a flat token stream to `[time, batch]`; if `args.cuda` is true, it moves the tensor to CUDA.
- `get_batch(source, i, args, seq_len=None, evaluation=False)` returns legacy autograd variables for a BPTT slice and next-token targets.
- `repackage_hidden(h)` detaches hidden states recursively so gradients stop at BPTT boundaries.

### Dropout helpers

- `embedded_dropout(embed, words, dropout=0.1, scale=None)` samples a mask over embedding rows, applies it to the embedding weight matrix, and then performs an embedding lookup.
- `LockedDropout.forward(x, dropout=0.5)` applies one dropout mask of shape `[1, batch, features]` across all time steps. It is inactive when the module is not training or dropout is zero.
- `mask2d(B, D, keep_prob, cuda=True)` creates a keep-probability mask shaped `[B, D]`; recurrent cells use it for cell-input and hidden-state masking.

### Experiment and checkpoint helpers

- `create_exp_dir(path, scripts_to_save=None)` creates the experiment directory and, when scripts are provided, copies them into a `scripts/` subdirectory.
- `save_checkpoint(model, optimizer, epoch, path, finetune=False)` writes full model and optimizer artifacts. Normal mode writes `model.pt`, `optimizer.pt`, and `misc.pt`; finetune mode writes `finetune_model.pt`, `finetune_optimizer.pt`, and still writes `misc.pt`.
- `misc.pt` stores `{'epoch': epoch + 1}` so resume and rollback logic can continue at the next epoch.
