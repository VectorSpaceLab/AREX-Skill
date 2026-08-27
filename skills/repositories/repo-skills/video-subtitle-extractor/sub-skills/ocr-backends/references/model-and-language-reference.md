# Model and Language Reference

## Bundled model families

VSE's baseline source includes PP-OCRv5 detection and recognition directories:

- Detection: `PP-OCRv5_mobile_det_infer`, `PP-OCRv5_server_det_infer`.
- General recognition: `PP-OCRv5_mobile_rec_infer`, `PP-OCRv5_server_rec_infer`.
- Language-group recognition: `korean_PP-OCRv5_mobile_rec_infer`,
  `latin_PP-OCRv5_mobile_rec_infer`, `arabic_PP-OCRv5_mobile_rec_infer`,
  `cyrillic_PP-OCRv5_mobile_rec_infer`, `devanagari_PP-OCRv5_mobile_rec_infer`,
  `th_PP-OCRv5_mobile_rec_infer`, `el_PP-OCRv5_mobile_rec_infer` when present.

`PaddleModelConfig` reads `Global.model_name` from each `inference.yml` when
available and passes model directory/name arguments to PaddleOCR 3.x APIs.

## Mode-to-model rules

| Mode | Detection model | Recognition model |
| --- | --- | --- |
| `fast` | mobile det if present, otherwise server det | Chinese/Traditional/English/Japanese use general mobile rec; other languages use their group model |
| `auto` | server det | language-specific server or group model |
| `accurate` | server det | language-specific server or group model |

## Language grouping

Representative mapping:

| Codes | Group |
| --- | --- |
| `ch`, `chinese_cht`, `en`, `japan` | general Chinese/English/Japanese models; Fast can use general mobile rec |
| `korean` | Korean mobile recognition |
| `ar`, `fa`, `ug`, `ur`, `ps`, `sd`, `bal` | Arabic group |
| `ru`, `rs_cyrillic`, `uk`, `bg`, and other Cyrillic codes | Cyrillic group |
| `de`, `es`, `fr`, `it`, `pt`, `vi`, `tr`, `latin`, and many European/Latin-script codes | Latin group |
| `hi`, `mr`, `ne`, `devanagari`, and related codes | Devanagari group |
| `th`, `el` | Thai / Greek-specific model when bundled |

Use `scripts/model_config_probe.py --repo-root <vse-source>` to inspect the
actual source tree's bundled directories and confirm a language/mode mapping
without running OCR.

## OCR thresholds and batches

Relevant config settings:

- `dropScore`: OCR result confidence threshold; default UI label is 75%.
- `recBatchNumber`: text boxes recognized at once; larger GPU memory can
  support higher values.
- `maxBatchSize`: DB detection batch size.
- `subtitleAreaDeviationRate`: allowed fraction outside selected subtitle area.
- `thresholdTextSimilarity`: post-OCR duplicate grouping strictness.

Route text cleanup effects to `postprocessing-config`; route frame sampling to
`extraction-workflows`.
