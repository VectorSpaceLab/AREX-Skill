# SynthDoG Workflows

## Purpose

Read this when you need a concrete command sequence for SynthDoG generation, a tiny smoke fixture, or the output layout that the template writes.

## Verified runtime facts

- The source template is driven by `synthtiger` and a `SynthDoG` template class.
- The save path creates `train/`, `validation/`, and `test/` splits under the output root.
- Each generated sample saves `image_<idx>.jpg` plus an appended `metadata.jsonl` entry.
- The `ground_truth` field stores a JSON string whose `gt_parse.text_sequence` value is the generated label.
- The CLI syntax from the source README is `synthtiger -o OUT -c COUNT -w WORKERS -v template.py SynthDoG config.yaml`.

## Render-then-run flow

Use the bundled placeholder configs together with the render helper before you call `synthtiger`:

```bash
python scripts/render_config.py \
  --language en \
  --resource-root ./resources \
  --output-config ./rendered/synthdog_en.yaml \
  --print-command

synthtiger -o ./outputs/synthdog_smoke -c 1 -w 1 -v scripts/template.py SynthDoG ./rendered/synthdog_en.yaml
```

If you already have separate asset directories, pass explicit overrides instead of `--resource-root`:

```bash
python scripts/render_config.py \
  --language ja \
  --background-dir ./external-assets/background \
  --paper-dir ./external-assets/paper \
  --corpus-file ./external-assets/corpus/jawiki.txt \
  --font-dir ./external-assets/font/ja \
  --output-config ./rendered/synthdog_ja.yaml
```

## Tiny-fixture smoke

- Use `-c 1 -w 1` for the smallest safe smoke.
- Add `-s 0` if you want a reproducible split choice while debugging.
- Expect only one split directory on a 1-sample run; the split choice is random and not all of `train/`, `validation/`, and `test/` will appear.
- Verify that `image_0.jpg` exists and that the matching `metadata.jsonl` line has both `file_name` and `ground_truth`.

## Custom corpus adaptation

- Prepare a UTF-8 plain-text corpus and a font directory that can render the characters in that corpus.
- Render a config with `scripts/render_config.py` and point `--corpus-file` and `--font-dir` at your custom assets.
- Run the generator from the sub-skill root so the bundled `scripts/template.py` and `references/configs/*.yaml` paths resolve naturally.
- If the generated text looks truncated or empty, increase font coverage first; only then tune layout knobs such as `text_scale`, `fill`, `max_row`, `max_col`, or `stack_spacing`.

## Output layout

```text
<output-root>/
  train/
    image_0.jpg
    metadata.jsonl
  validation/
    image_1.jpg
    metadata.jsonl
  test/
    image_2.jpg
    metadata.jsonl
```

The template appends one JSON line per sample. If you reuse the same output directory, clean it first or write to a fresh path so old `metadata.jsonl` rows do not accumulate unexpectedly.
