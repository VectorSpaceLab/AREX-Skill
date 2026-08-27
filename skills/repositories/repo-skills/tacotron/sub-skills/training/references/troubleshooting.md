# Training troubleshooting

- **Metadata cannot load:** run the data validator; `DataFeeder` resolves array
  filenames relative to the directory containing the input metadata.
- **CMUdict exception:** with `use_cmudict=True`, the file must be named
  `cmudict-0.7b` beside the metadata. Fix placement or disable the option
  intentionally.
- **Incompatible shapes:** long audio exceeds the decoder limit. Calculate the
  duration from `max_iters`, `outputs_per_step`, and `frame_shift_ms`; increase
  max_iters or curate the data, then use the same value at eval.
- **Loss explodes or attention is lost:** inspect the loss threshold and
  alignment images, stop the run, and restore from a checkpoint before the
  spike if available. Do not treat a later recovery as proof that the run is
  healthy.
- **Restore path not found:** the script constructs `model.ckpt-<step>` under
  the selected log directory. Confirm `--name`, `--base_dir`, and step number.
- **No TensorBoard/audio artifact:** verify the process reached a checkpoint
  interval and that the log directory is writable; these are not produced at
  every step.
- **Dirty Git failure:** remove `--git` for an exploratory run or commit/stash
  changes deliberately. Never disable the check while claiming provenance.
