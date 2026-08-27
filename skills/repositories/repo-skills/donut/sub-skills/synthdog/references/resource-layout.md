# SynthDoG Resource Layout

## Purpose

Read this when you need to prepare backgrounds, paper textures, corpora, or fonts for SynthDoG, or when you need to know whether the original asset bundle was copied.

## Bundling decision

Large resource assets are **reference-only** here. No background images, paper textures, corpora, or fonts are copied into the runtime skill tree by default.

Why:

- The source asset bundle is large enough that copying every binary would bloat the skill tree.
- The resource set is user- and language-specific, so a generic copy would still leave many real runs incomplete.
- `scripts/render_config.py` accepts external resource directories, so future agents can point at copied or custom assets without reopening the source checkout.

## Expected runtime layout

If you want to stage assets locally for the bundled configs, use a tree like this anywhere you control:

```text
resources/
  background/
    *.jpg|*.jpeg|*.png
  paper/
    *.jpg|*.jpeg|*.png
  corpus/
    enwiki.txt
    jawiki.txt
    kowiki.txt
    zhwiki.txt
  font/
    en/
      *.ttf|*.otf
    ja/
      *.ttf|*.otf
    ko/
      *.ttf|*.otf
    zh/
      *.ttf|*.otf
```

The render helper will accept either the root `resources/` directory or explicit `--background-dir`, `--paper-dir`, `--corpus-file`, and `--font-dir` overrides.

## Minimal tiny-fixture set

For the smallest smoke test, you only need:

- one background image
- one paper texture
- one short UTF-8 corpus file
- one font directory with at least one font that can render the selected corpus

That tiny set is enough to exercise the CLI, template imports, and metadata writing without copying the full source asset bundle.

## Template flow

```text
background texture -> paper texture -> text layout -> document effects -> final image -> metadata.jsonl
```

`Background` creates the background layer, `Document` creates the page and content layers, `Content` reads characters from the corpus, and `Grid` / `GridStack` decide how the text boxes are arranged.
