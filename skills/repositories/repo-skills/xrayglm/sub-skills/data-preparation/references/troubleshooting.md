# Data-preparation troubleshooting

## `malformed JSON`

The helpers use UTF-8 JSON and report the line and column returned by the
parser. Check for a truncated download, a missing comma, a pasted Markdown
fence, or a JSON file that was actually saved as plain text. Re-export the
source as valid JSON and rerun validation. Do not use `eval`, permissive repair,
or a positional text scrape to bypass the error.

## Wrong top-level shape

An OpenI source must be an object with an `annotations` array. A training file
must be an array of objects. `convert_xray_json.py` intentionally accepts the
wrapper only; `merge_xray_records.py` expects records as its first input and a
wrapper or keyed caption array as its second. Confirm which file is English,
Chinese, wrapper, or already converted before choosing a command.

## Missing fields or empty text

Every annotation needs a non-empty string `image_id` and `caption`. Every
training item needs non-empty string `img`, `prompt`, and `label`. Numeric IDs
must be represented as strings if they are to be used as keys. Empty captions
are not harmless placeholders: stop and fix or explicitly exclude the source
item upstream.

## Duplicate image IDs

A duplicate can arise when XML records contain repeated image references, when
separate translation batches are concatenated, or when two paths have the same
filename stem. The validator, converter, and merger fail with both the later
and first locations. Deduplicate using the approved source key and review the
content; never keep the first item silently.

## Caption count or key mismatch

The merger does not zip arrays. By default it requires equal lengths and exact
key sets. A shorter translation file commonly means an external request failed
partway through. Re-run or repair that job and preserve its keyed output. If a
partial update is intentional, pass `--allow-length-mismatch`; unknown keys
still fail and unmatched records remain unchanged. Review the helper's note
before using the result.

## Output equals input / overwrite refusal

The converter and merger refuse an existing output unless `--force` is given,
and detect an output path that resolves to an input path. Prefer a new output
for rollback and audit. If in-place replacement is genuinely approved, first
validate the inputs, confirm the exact path, then use `--force`; a failed
validation never opens the output.

## Missing images

A valid record schema does not guarantee image availability. Use:

```bash
python /abs/path/to/validate_xray_records.py records.json \
  --check-images --base-dir /approved/image/base
```

The report lists every missing path. Relative paths are based on `--base-dir`,
not on the directory containing the JSON file. Check for a wrong base, a
missing `.png` suffix, case-sensitive filename differences, or an unapproved
acquisition. Do not solve the problem by downloading or copying files here.

## Path-base confusion

The source convention `./data/Xray/162_1.png` is relative to the process
working directory in the original training code. A helper invoked from another
cwd will not reinterpret it relative to the checkout. Supply the intended
`--base-dir` for checks and use `--image-template` during conversion if the
consumer needs a different path convention. Avoid absolute checkout paths in
portable manifests.

## Translation limits and credentials

`data/translation_en2zh.py` demonstrates an external OpenAI ChatCompletion
step and has a key placeholder. It is not a safe runtime dependency. Never
place credentials in scripts, prompts, labels, or generated records. Stop when
there is no approved provider, credential, privacy decision, rate-limit plan,
model/version record, or way to audit failed requests. Local helpers can
validate and merge a completed keyed translation, but cannot assess its
medical fidelity or perform translation.

## Fine-tuning and inference boundaries

If records validate but training fails, hand the issue to the fine-tuning
owner: this skill does not install model dependencies, inspect adapters, or
change `finetune_XrayGLM.py`. If a prompt or image is needed for a live model
conversation, hand it to inference; do not add runtime behavior to these data
helpers.
