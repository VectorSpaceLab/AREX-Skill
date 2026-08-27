# Modernization Notes

Use these notes when adapting the legacy deepjazz LSTM generation workflow to Python 3, modern Keras, or TensorFlow while preserving behavior that matters to the grammar pipeline.

## Preserve these invariants

- The grammar/token pipeline must still produce a flat corpus of token strings.
- `val_indices` and `indices_val` must remain inverse mappings for the active corpus.
- The generation path must still build one-hot tensors with the same logical shapes.
- The end result must still be a MIDI write after pruning and note reconstruction.

## Legacy-to-modern migration points

### 1) Keras API updates

- `nb_epoch` becomes `epochs`.
- Legacy `keras.layers.core` / `keras.layers.recurrent` imports should be updated to modern equivalents.
- `rmsprop` remains a valid optimizer name, but the import style may differ.

### 2) NumPy compatibility

- Replace `np.bool` with `bool` or `np.bool_`.
- Keep tensor dtypes explicit to avoid silent changes in later NumPy releases.

### 3) Python 3 compatibility

- Replace `xrange` with `range`.
- Replace `itertools.izip_longest` with `itertools.zip_longest`.
- Audit any legacy `print` or iterator assumptions when porting helper code.

### 4) Backend selection

- The legacy path expects Theano through `KERAS_BACKEND=theano`.
- A modern TensorFlow port should remove the Theano-specific backend assumptions.
- Do not keep old CUDA/Theano flags as if they were portable to modern TensorFlow.

### 5) Corpus mapping stability

The historical code derives `values` from a set. That keeps the vocabulary content but not a guaranteed ordering. For a modern retrain, you may keep that behavior if you want exact legacy semantics; for reproducibility across runs, you may choose a stable order such as `sorted(set(corpus))`, but that changes index assignments and invalidates old weights.

## Modernization approach for `tf.keras`

A direct port usually keeps the same model shape but updates the API calls:

- `Sequential`
- `LSTM(128, return_sequences=True, input_shape=(max_len, vocab_size))`
- `Dropout(0.2)`
- `LSTM(128)`
- `Dropout(0.2)`
- `Dense(vocab_size, activation='softmax')`
- `model.compile(loss='categorical_crossentropy', optimizer='rmsprop')`
- `model.fit(X, y, batch_size=128, epochs=N_epochs)`

## Playback and output modernization

- Keep realtime playback optional.
- Prefer an explicit `.midi` output filename and a caller-controlled output directory.
- Avoid coupling model training to playback in a single mandatory function when porting to headless or notebook environments.

## Recommended modernization sequence

1. Preserve the corpus/token pipeline.
2. Port the model API and dtypes.
3. Remove Python 2-specific iterator usage.
4. Make playback optional.
5. Validate that the output MIDI still reflects the same grammar and pruning stages.
