# CLI reference for pretrained inference

## `asteroid-infer`

```bash
asteroid-infer URL_OR_PATH --files FILES [FILES ...] [options]
```

Important options:

- `--files`: one or more filenames, directory names, or globs
- `--force-overwrite` / `-f`: overwrite existing `*_estN.wav` outputs
- `--resample` / `-r`: resample mismatched input sample rates automatically
- `--ola-window` / `-w`: enable overlap-add chunking
- `--ola-hop`: hop size for overlap-add; defaults to half the window
- `--ola-window-type`: window shape for overlap-add
- `--ola-no-reorder`: disable chunk reordering inside overlap-add
- `--output-dir` / `-o`: write outputs into a separate directory
- `--device` / `-d`: explicit device, for example `cpu` or `cuda:0`

The CLI defaults to CUDA when available and CPU otherwise.

## `asteroid-versions`

Prints Asteroid, PyTorch, and PyTorch-Lightning versions, which is useful when comparing a local environment against the repo snapshot.

## File output convention

For file inputs, the CLI writes one WAV per source using the pattern:

- `<input_basename>_est1.wav`
- `<input_basename>_est2.wav`
- ...

If `--output-dir` is set, the files are written there instead of next to the input.
