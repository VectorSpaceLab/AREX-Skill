# Model API and shapes

## `models.create_model(name, hparams)`

The only registered name is `tacotron`; other names raise `Exception('Unknown
model: ...')`. It returns a `Tacotron` object.

## `Tacotron.initialize`

Inputs:

- `inputs`: `int32`, shape `[N, T_in]`, symbol ids.
- `input_lengths`: `int32`, shape `[N]`.
- `mel_targets`: optional `float32`, `[N, T_out, num_mels]`.
- `linear_targets`: optional `float32`, `[N, T_out, num_freq]`.

After initialization, the object exposes `inputs`, `input_lengths`,
`mel_outputs`, `linear_outputs`, `alignments`, and target fields. The output
mel shape is `[N, T_out, num_mels]`; linear output is `[N, T_out, num_freq]`;
alignment is batch/encoder/decoder oriented after transpose.

## Training additions

Call `add_loss()` only after initializing with targets. It creates `mel_loss`,
`linear_loss`, and `loss`. Call `add_optimizer(global_step)` after loss; it
creates `learning_rate`, clipped `gradients`, and `optimize`.

## Audio helpers

`audio.spectrogram(wav)` and `audio.melspectrogram(wav)` return normalized
frequency-by-time matrices before preprocessing transposes them for disk.
`audio.find_endpoint(wav)` trims a sufficiently quiet tail. The hparams
`num_freq`, `num_mels`, sample rate, frame length, and frame shift must match
these helpers.
