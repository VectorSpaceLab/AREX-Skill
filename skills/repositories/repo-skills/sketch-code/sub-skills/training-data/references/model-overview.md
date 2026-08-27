# SketchCode model overview

SketchCode trains an image-captioning style model: a CNN encodes the wireframe image, a GRU stack encodes the partial GUI token sequence, and a GRU decoder predicts the next GUI vocabulary token.

## Constants and sequence lengths

| Constant | Value | Role |
| --- | --- | --- |
| `MAX_LENGTH` | `48` | Language input length used by the model. The generator keeps the last 48 padded tokens. |
| `MAX_SEQ` | `150` | Maximum sequence length passed to `pad_sequences` before the last 48 tokens are selected. |
| `BATCH_SIZE` | `64` | Used to compute `steps_per_epoch` as total token count divided by 64. |

## Image encoder

Input shape:

```text
(256, 256, 3)
```

Encoder structure:

1. `Conv2D(16, (3, 3), padding='valid', activation='relu')`
2. `Conv2D(16, (3, 3), padding='same', strides=2, activation='relu')`
3. `Conv2D(32, (3, 3), padding='same', activation='relu')`
4. `Conv2D(32, (3, 3), padding='same', strides=2, activation='relu')`
5. `Conv2D(64, (3, 3), padding='same', activation='relu')`
6. `Conv2D(64, (3, 3), padding='same', strides=2, activation='relu')`
7. `Conv2D(128, (3, 3), padding='same', activation='relu')`
8. `Flatten()`
9. `Dense(1024, activation='relu')`
10. `Dropout(0.3)`
11. `Dense(1024, activation='relu')`
12. `Dropout(0.3)`
13. `RepeatVector(48)`

The repeated image representation is concatenated with the language representation at every decoder time step.

## Language encoder

Language input shape:

```text
(48,)
```

Structure:

1. `Embedding(vocab_size, 50, input_length=48, mask_zero=True)`
2. `GRU(128, return_sequences=True)`
3. `GRU(128, return_sequences=True)`

The vocabulary size is computed from the single-line `vocabulary.vocab` plus one reserved zero/padding index.

## Decoder and output

The decoder concatenates the repeated image encoding and language encoding, then applies:

1. `GRU(512, return_sequences=True)`
2. `GRU(512, return_sequences=False)`
3. `Dense(vocab_size, activation='softmax')`

The model predicts the next token as a categorical distribution over the vocabulary.

## Optimizer and loss

Both newly created and loaded pretrained models are compiled with:

```text
loss = categorical_crossentropy
optimizer = RMSprop(lr=0.0001, clipvalue=1.0)
```

## Training generator behavior

For each GUI token sequence, the generator creates next-token training examples from prefixes:

```text
<START> token_1 token_2 ... token_n <END>
```

For each prefix, the model sees:

- The image feature array from `sample_id.npz`.
- The padded prefix sequence, truncated to the last 48 tokens.
- A one-hot target for the next vocabulary token.

The implementation iterates one GUI/image sample at a time, yields all prefix examples for that sample, and uses `steps_per_epoch = total_sequence_token_count // 64`.

## Save and callback outputs

At the end of training, the model writes:

```text
model_json.json
weights.h5
```

During training, callbacks also write:

```text
training_val_losses.csv
weights-epoch-####--val_loss-####--loss-####.h5
```

Checkpoint weights are configured as best-only and written every two epochs in the historical Keras callback configuration.

## Practical implications

- Memory use is dominated by `256x256x3` image arrays, the convolutional stack, and many prefix examples per GUI sequence.
- Very small datasets can produce `steps_per_epoch` or `validation_steps` values that are zero if total token count is below `BATCH_SIZE`; increase data, reduce batch size in a code patch, or use a bounded smoke-only plan instead of a real training run.
- The code targets old Keras/TensorFlow APIs such as `fit_generator`, `period` in `ModelCheckpoint`, and `RMSprop(lr=...)`; modern runtimes may require compatibility fixes.
