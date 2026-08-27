# SynthDoG Configuration

## Purpose

Read this when you need to choose the English/Japanese/Korean/Chinese bundle, adjust the geometry or augmentation knobs, or adapt SynthDoG for a custom corpus.

## Template bundles

The bundled config files are placeholder templates. Render them with `scripts/render_config.py` before running `synthtiger`.

| Template file | Language | Default corpus filename | Default font directory | Notes |
| --- | --- | --- | --- | --- |
| `references/configs/config_en.yaml` | English | `enwiki.txt` | `font/en/` | English text + Latin fonts |
| `references/configs/config_ja.yaml` | Japanese | `jawiki.txt` | `font/ja/` | Japanese text + JP fonts |
| `references/configs/config_ko.yaml` | Korean | `kowiki.txt` | `font/ko/` | Korean text + KR fonts |
| `references/configs/config_zh.yaml` | Chinese | `zhwiki.txt` | `font/zh/` | Chinese text + SC fonts |

## Placeholder tokens

The bundled config templates use four placeholder tokens that `scripts/render_config.py` replaces with actual paths:

| Token | Replaces |
| --- | --- |
| `__BACKGROUND_DIR__` | Background texture directory |
| `__PAPER_DIR__` | Paper texture directory |
| `__CORPUS_FILE__` | UTF-8 corpus file |
| `__FONT_DIR__` | Language font directory |

## Config layers

| Layer | Main keys | What they control |
| --- | --- | --- |
| Global generator | `quality`, `landscape`, `short_size`, `aspect_ratio` | JPEG quality and overall output canvas geometry |
| `background` | `image.paths`, `image.weights`, `effect.args` | Background texture selection and blur |
| `document` | `fullscreen`, `landscape`, `short_size`, `aspect_ratio`, `paper`, `content`, `effect` | Page size and document-level augmentation |
| `document.paper` | `image.paths`, `alpha`, `grayscale`, `crop` | Paper texture and blending |
| `document.content.text` | `path` | Plain-text corpus source |
| `document.content.font` | `paths`, `weights`, `bold` | Font directories and sampling weights |
| `document.content.layout` | `text_scale`, `max_row`, `max_col`, `fill`, `full`, `align`, `stack_spacing`, `stack_fill`, `stack_full` | Grid and stacked-block layout behavior |
| `document.content.textbox` | `fill` | How much of each text cell can be filled |
| `document.content.textbox_color` / `content_color` | `prob`, `args` | Character color variation |
| `document.effect` | elastic distortion, noise, perspective | Document warping before the global image effect |
| `effect` | color, shadow, contrast, brightness, motion blur, gaussian blur | Final visual variation |

## Geometry knobs that matter most

- `short_size` and `aspect_ratio` choose the overall output size.
- `document.fullscreen` decides whether the document fills the page or is resized into a smaller region.
- `document.landscape` and the top-level `landscape` decide orientation.
- `text_scale`, `fill`, `stack_fill`, and `stack_spacing` control how dense the text blocks become.
- `max_row` and `max_col` cap how many cells the grid can generate.
- `align` can be `left`, `right`, or `center` per block.

## Custom corpus checklist

1. Supply a UTF-8 plain-text corpus with the glyphs you want to render.
2. Point `--font-dir` at a directory with fonts that support those glyphs.
3. Keep background and paper textures separate from the corpus and font assets.
4. Render the template with `scripts/render_config.py` before you run `synthtiger`.
5. Start with a tiny smoke run so you can inspect truncation, missing glyphs, or layout imbalance before generating a larger dataset.

## Output behavior to remember

- The `SynthDoG` template writes the `train/`, `validation/`, and `test/` split directories itself.
- Metadata rows are appended as JSON lines.
- Labels are whitespace-normalized before they are written into `gt_parse.text_sequence`.
- The template computes an ROI from the paper quad internally, but the saved metadata only includes the image file name and ground-truth text sequence.
