# EasyOCR CLI Reference

The installed console command is `easyocr`.

## Minimal shape

```bash
easyocr -l en -f path/to/image.png
```

## Required flags

- `-l / --lang` — one or more language codes.
- `-f / --file` — input image path.

## Option groups

### Runtime and model selection

- `--gpu` — backend hint; the source parser is brittle, so prefer the Python
  API when you need exact falsey behavior.
- `--model_storage_directory` — detector and recognizer weight cache.
- `--user_network_directory` — custom recognition bundle directory.
- `--recog_network` — built-in or custom recognizer name.
- `--download_enabled` — allow model downloads when the cache is missing.
- `--detector` / `--recognizer` — enable or disable the detector or recognizer
  path.
- `--verbose` — logging verbosity.
- `--quantize` — intended CPU quantization switch, but see the troubleshooting
  note about the current tuple bug.

### OCR behavior

- `--decoder` — `greedy`, `beamsearch`, or `wordbeamsearch`.
- `--beamWidth` — beam width for beam search.
- `--batch_size` and `--workers` — throughput tuning.
- `--allowlist` / `--blocklist` — character filters.
- `--detail` — `0` for strings, `1` for structured results.
- `--rotation_info` — intended rotation list, but the current parser uses
  `type=list`, so prefer the Python API for this option.
- `--paragraph`, `--min_size`, `--contrast_ths`, `--adjust_contrast`,
  `--text_threshold`, `--low_text`, `--link_threshold`, `--canvas_size`,
  `--mag_ratio`, `--slope_ths`, `--ycenter_ths`, `--height_ths`,
  `--width_ths`, `--y_ths`, `--x_ths`, and `--add_margin` — detection and
  grouping controls mirrored from the Python API.
- `--output_format` — `standard`, `dict`, or `json`.

## CLI caveats

- Several boolean-like flags are declared with `type=bool`, so non-empty strings
  such as `False` or `0` still behave as truthy values.
- `--rotation_info` is not parsed as a Python list literal.
- If you need exact control over backend choice, rotated crops, or falsey flag
  values, use the Python API or the bundled smoke scripts instead of the raw
  parser.

## Related references

- `api-reference.md` for the `Reader` API surface.
- `configuration.md` for backend and model-selection rules.
- `sub-skills/inference/references/workflows.md` for practical examples.
