# Safe data workflows

## Local inspection first

1. Identify the actual input shape before transforming it. Use the wrapper
   shape for `data/openi-en.json` and `data/Xray/openi-zh.json`; use the array
   shape for `data/openi-ch-random.json` and `data/demo/dataset.json`.
2. Run the validator against the source. It reports all structural failures,
   rather than stopping at the first bad item. For a wrapper, validation checks
   `image_id` and `caption`; for a record array, it checks `img`, `prompt`, and
   `label`.
3. Decide the image base explicitly. The source builders write
   `./data/Xray/{image_id}.png`, but that is a path convention, not proof that
   the image tree exists in the current working directory.

Example from an arbitrary working directory:

```bash
python /abs/path/to/validate_xray_records.py \
  /abs/path/to/data/openi-ch-random.json \
  --check-images --base-dir /abs/path/to/XrayGLM
```

A wrapper cannot be image-checked because it contains IDs and captions rather
than paths. Convert it first, or check the approved image acquisition
separately.

## Wrapper to records

Use a new output path and inspect it before training:

```bash
python /abs/path/to/convert_xray_json.py \
  /abs/path/to/data/Xray/openi-zh.json /tmp/openi-zh-records.json \
  --prompt-index 0
python /abs/path/to/validate_xray_records.py /tmp/openi-zh-records.json \
  --check-images --base-dir /abs/path/to/XrayGLM
```

Use `--prompt-index 1` through `5` only when the selected prompt is a known
experiment variable. The six variants are source-derived, but some are generic
background-description prompts and are not equivalent to a diagnostic prompt.
Do not call the original random builder for a reproducible manifest.

To produce a caption archive or human review artifact instead:

```bash
python /abs/path/to/convert_xray_json.py SOURCE.json captions.json --format captions
python /abs/path/to/convert_xray_json.py SOURCE.json captions.md --format markdown
```

The converter validates all IDs and captions before writing. If an output
already exists, choose another path or deliberately pass `--force`.

## Keyed caption merge

Keep the original record array and caption source intact. First validate the
caption source, then merge by image ID:

```bash
python /abs/path/to/merge_xray_records.py \
  /abs/path/to/openi-records.json /abs/path/to/translated-captions.json \
  /abs/path/to/openi-zh-merged.json
python /abs/path/to/validate_xray_records.py /abs/path/to/openi-zh-merged.json
```

The default operation requires equal counts and an exact key set. This catches
truncated translation batches and prevents accidental positional alignment.
If a deliberately partial caption set is being applied, use
`--allow-length-mismatch`; the helper still rejects duplicate and unknown
caption keys and prints how many records were retained unchanged. Review those
records before any training run.

The merger accepts an OpenI wrapper or a JSON list of `{image_id, caption}`
objects. Markdown is a review/export format and should not be parsed back into
training data: use the keyed JSON output of the conversion step.

## Acquisition and translation boundaries

The repository's XML helper expects a locally acquired XML tree and a local
PNG tree; its copy behavior is not part of this skill. The image-copy helper
also assumes `./images` and writes into `./images2`. Do not guess either base,
run bulk copies, or overwrite a dataset tree. An approved acquisition process
must supply the files, license/provenance, and the final base directory.

The translation helper embeds an API-key placeholder and calls an external
ChatCompletion API. Do not copy it into an offline runtime, put a key in JSON,
or treat a placeholder as working credentials. Stop for absent credentials,
provider approval, privacy review, quotas, or an unrecorded model/version.
After an external translation job, save a keyed JSON result, check its count
and unique IDs, and merge it with the local helper.

## Handoff checklist

- source path and source shape recorded;
- output path is distinct or `--force` is explicitly approved;
- record count and unique image-key count reported;
- prompt index or explicit prompt recorded;
- image base and `--check-images` result recorded;
- external acquisition/translation gaps and credentials status recorded;
- final array validated before handing it to fine-tuning.
