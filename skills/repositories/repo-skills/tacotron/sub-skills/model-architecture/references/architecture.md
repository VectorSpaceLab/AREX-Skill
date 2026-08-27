# Tacotron graph architecture

## High-level flow

Integer symbol ids are embedded, passed through a two-layer prenet, and encoded
by a CBHG block. Location-sensitive attention is not the default here: the
implementation uses `BahdanauAttention` in a TensorFlow contrib
`AttentionWrapper`, followed by a decoder prenet and concatenation of decoder
output with attention context.

The decoder is a three-layer GRU stack: an output-projected concatenated
attention cell followed by two residual GRUs. It emits `outputs_per_step` mel
frames per decoder step. A postnet CBHG converts mel outputs to linear
spectrogram outputs, and alignment history is exposed as `alignments`.

## Training vs inference

`linear_targets is not None` selects training mode. Training uses target mel
frames through `TacoTrainingHelper`, adds L1 mel and linear losses, and applies
Adam with global-norm clipping. Inference uses `TacoTestHelper`, feeds predicted
mel frames back to the decoder, and stops at EOS-like all-zero frames or
`max_iters`.

## Audio reconstruction

The default hparams are sample rate 20000, 80 mel bins, 1025 linear bins, 50 ms
frame length, 12.5 ms shift, preemphasis 0.97, 60 Griffin-Lim iterations, and
power 1.5. `util.audio.inv_spectrogram` performs NumPy/librosa reconstruction;
the TensorFlow path returns a preemphasized signal and the caller applies
`inv_preemphasis`.

Changing spectrogram dimensions or audio hparams invalidates assumptions in
both data arrays and model checkpoints. Keep the configuration used for
preprocessing, training, evaluation, and serving aligned.
