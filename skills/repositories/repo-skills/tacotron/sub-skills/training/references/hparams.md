# Hyperparameters and invariants

Important defaults from `hparams.py`:

- Text: `cleaners=english_cleaners`, `use_cmudict=False`.
- Audio: `num_mels=80`, `num_freq=1025`, `sample_rate=20000`,
  `frame_length_ms=50`, `frame_shift_ms=12.5`, `preemphasis=0.97`.
- Model: `outputs_per_step=5`, embed/prenet/encoder/postnet/attention/decoder
  depths of 256 except the second prenet layer of 128.
- Training: `batch_size=32`, Adam betas `.9/.999`, initial learning rate `.002`,
  decayed by the Noam-style schedule unless disabled.
- Evaluation: `max_iters=200`, `griffin_lim_iters=60`, `power=1.5`.

The maximum nominal audio duration is:

```text
max_iters * outputs_per_step * frame_shift_ms milliseconds
```

With defaults this is 12.5 seconds. Set `max_iters` high enough for the longest
training/eval utterance, but understand the memory and decode-time cost. Hparam
values are parsed by TensorFlow's HParams implementation; use the repository's
comma-separated syntax, for example `batch_size=16,outputs_per_step=2`.
