# Asset layout

This repository is a bilingual diagram atlas, so asset maintenance is mostly about keeping file trees, workbook-backed names, and rendered image variants aligned.

## Top-level asset families

| Area | Role | Maintenance notes |
| --- | --- | --- |
| `images_chinese/png_big/` | Canonical high-resolution Chinese PNG renders | 121 files. These are the main image targets referenced by `README.md`. |
| `images_chinese/png_small/` | Preview-size Chinese PNG renders | 120 files. These should mirror `png_big/` except for the special roadmap asset below. |
| `images_chinese/source_svg/` | Chinese editable vector sources | 121 files. In the current tree this mirrors `png_big/` 1:1, including the roadmap asset. |
| `images_english/png_big/` | Canonical high-resolution English PNG renders | 116 files. These should mirror `png_small/` 1:1. |
| `images_english/png_small/` | Preview-size English PNG renders | 116 files. These are the image targets used by `src/README_EN.md`. |
| `images_english/source_svg/` | English editable vector sources | 114 files. Two RoPE figures are backed by workbook sources instead of SVG sources. |
| `images_english/source_xlsx/` | Workbook-based source diagrams | 2 files: `rope.xlsx` and `rope-2.xlsx`. Treat these as source artifacts, not slide exports. |
| `src/assets/` | Banners, covers, QR images, and presentation templates | Includes the hero SVGs under `banner/`, plus `banner.pptx` and `images-template.pptx`. These are support assets, not slide exports. |
| `src/conf/info-ch.xlsx`, `src/conf/info-en.xlsx` | Headerless naming maps used by the maintenance scripts | These workbooks drive slide-number-to-name renames. Row 1 corresponds to slide 1. |
| PDF anchors in the repo root and `src/` | Book/roadmap anchors referenced by the README files | Keep them as reference anchors; do not treat them as mutable runtime inputs. |

## Naming conventions

- Chinese image stems usually begin with a section tag such as `【DPO】`, `【强化学习基础】`, or `【LLM基础拓展】`.
- English image stems usually begin with a section tag such as `【DPO】` or `【RL basics】`.
- `png_big`, `png_small`, and `source_svg` should keep the same stem for the same figure family.
- `source_xlsx` is different: its stems are workbook slugs such as `rope` and `rope-2`, not slide-style figure names.
- File names may contain spaces, full-width punctuation, Chinese characters, and mixed-language titles. Preserve the exact workbook text instead of normalizing it.
- The legacy source scripts use numeric slide prefixes like `幻灯片1`. The bundled helper should preview those renames before applying them.

## Workbook assumptions

The naming workbooks are headerless and simple:

- Column 1: top-level category or section label.
- Column 2: short figure title.
- Column 3: the generated display name used for image stems.
- Later columns may contain descriptive or legacy variants and should be preserved.

Current workbook drift to expect:

- Chinese workbook rows: 120.
- English workbook rows: 116.
- Chinese `png_big` has one extra figure, `AI Roadmap(AI知识架构).png`, which is not represented in `info-ch.xlsx`.
- English `source_svg` has two fewer figures than `png_big` because the two RoPE figures are backed by `source_xlsx/` instead.

## Generated versus source assets

| Type | Examples | Mutation rule |
| --- | --- | --- |
| Generated renders | `png_big/`, `png_small/` | Safe to rename only through dry-run-first helpers. |
| Editable sources | `source_svg/`, `source_xlsx/` | Preserve the source tree structure; do not assume every figure has both SVG and workbook sources. |
| Support materials | `src/assets/` | Keep banner/template assets separate from slide-figure maintenance. |
| Documentation anchors | PDFs in the repo root and under `src/` | Treat as reference sources for the atlas, not as rename targets. |

## Evidence notes

Provenance consulted while distilling this layout: `README.md`, `src/README_EN.md`, `src/conf/info-ch.xlsx`, `src/conf/info-en.xlsx`, `images_chinese/`, `images_english/`, `src/assets/`, `src/clip_images.py`, and `src/rename_images.py`.
