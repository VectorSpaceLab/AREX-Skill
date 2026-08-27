# LSTM Architecture

This reference captures the legacy model-building contract and the tensor shapes used by deepjazz's LSTM generation path.

## Public API

`build_model(corpus, val_indices, max_len, N_epochs=128)`

### Inputs

- `corpus`: flat list of grammar tokens, usually produced by splitting abstract grammar strings.
- `val_indices`: token-to-index mapping used to one-hot encode both inputs and labels.
- `max_len`: sequence length for truncated training windows.
- `N_epochs`: number of training epochs passed to the legacy Keras fit call.

### Derived vocabulary

- `N_values = len(set(corpus))`
- The legacy code uses the token set to define the vocabulary size.
- Preserve the same corpus/value mapping when modernizing a saved model or a coupled grammar pipeline.

## Training tensor construction

- Step size: `3`
- Training windows:
  - `sentences.append(corpus[i:i + max_len])`
  - `next_values.append(corpus[i + max_len])`
- Loop range: `0` to `len(corpus) - max_len`
- Input tensor `X` shape: `(num_sentences, max_len, N_values)`
- Label tensor `y` shape: `(num_sentences, N_values)`
- Legacy dtype: `np.bool`

### One-hot fill pattern

- `X[i, t, val_indices[val]] = 1`
- `y[i, val_indices[next_values[i]]] = 1`

## Model stack

1. `Sequential()`
2. `LSTM(128, return_sequences=True, input_shape=(max_len, N_values))`
3. `Dropout(0.2)`
4. `LSTM(128, return_sequences=False)`
5. `Dropout(0.2)`
6. `Dense(N_values)`
7. `Activation('softmax')`

### Compile and fit

- Loss: `categorical_crossentropy`
- Optimizer: `rmsprop`
- Batch size: `128`
- Epoch argument: `nb_epoch=N_epochs`

## Inference shape expectations

- Generation builds a single-sequence tensor with shape `(1, max_len, vocab_size)`.
- The model returns a probability vector of shape `(1, vocab_size)`.
- Sampling uses temperature/diversity scaling and then selects the next token index.

## Preservation rules for modernization

When porting this model to modern Keras or TensorFlow:

- Keep the exact token mapping used by the corpus unless you are intentionally retraining from scratch.
- Keep the grammar pipeline and output-token semantics unchanged.
- Replace legacy API names without changing the meaning of the architecture.
- Preserve sequence length, vocabulary size, and output dimensionality relationships.
