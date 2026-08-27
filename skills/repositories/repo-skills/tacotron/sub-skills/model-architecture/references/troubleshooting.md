# Model troubleshooting

- **`tf.contrib` missing:** use TensorFlow 1.x; this graph imports contrib RNN,
  seq2seq, signal, and HParams APIs.
- **Unknown model:** pass exactly `tacotron` to `create_model` or extend the
  model registry deliberately.
- **Shape mismatch at initialization:** verify batch rank, input lengths, and
  target feature dimensions against `num_mels`/`num_freq`. Do not feed
  frequency-by-time arrays where time-major targets are expected.
- **Checkpoint restore fails after hparam changes:** checkpoints encode the
  original variable shapes. Restore with the training hparams or retrain under
  the changed dimensions; changing only the eval command is not a migration.
- **Poor or truncated audio:** check sample rate, frame shift, `max_iters`,
  Griffin-Lim iterations, and inverse preemphasis. A valid graph does not imply
  a valid trained checkpoint.
- **Out-of-memory graph/run:** reduce batch size or use a performance-capable
  GPU environment only after preserving the model/data shape contract.
