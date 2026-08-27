# Synthesis troubleshooting

- **Checkpoint not found:** pass a checkpoint prefix such as
  `model.ckpt-185000`, verify sidecar files, and check that the directory is
  writable for eval outputs.
- **Restore shape error:** use the training hparams, especially audio feature
  dimensions, model depths, `outputs_per_step`, and symbol vocabulary.
- **Empty text request:** the Falcon route intentionally rejects missing/empty
  `text`; URL-encode punctuation and inspect the response status.
- **Silent/truncated WAV:** confirm a trained checkpoint, endpoint trimming,
  sample rate, `max_iters`, and Griffin-Lim settings. A successful HTTP response
  can still contain poor model output.
- **Server starts then crashes:** inspect TensorFlow 1.x imports, checkpoint
  loading, and old Falcon compatibility before changing route code.
- **Unsafe exposure:** the demo binds `0.0.0.0` and has no authentication. Keep
  it local or place it behind an intentionally configured access boundary.
- **Text pronunciation differs:** use the text-normalization route and keep
  cleaner configuration synchronized with training.
