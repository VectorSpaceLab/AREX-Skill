# Config Reference

Important settings that affect post-processing and filtering:

| Setting | Effect |
| --- | --- |
| `generateTxt` | Writes a `.txt` file beside the generated SRT. |
| `wordSegmentation` | Runs subtitle text cleanup/segmentation after SRT generation. |
| `thresholdTextSimilarity` | Determines whether consecutive OCR lines are considered the same subtitle. Higher is stricter. |
| `dropScore` | Drops OCR boxes below this confidence. |
| `subtitleAreaDeviationRate` | Allows a recognized text box to exceed the selected area by a configured fraction. |
| `subtitleAreaDeviationPixel` | Expands detected subtitle-area filtering during scene-text cleanup. |
| `waterarkAreaNum` | Number of likely watermark areas presented for filtering. |
| `debugOcrLoss` | Emits debug images for lost CJK subtitle frames when applicable. |
| `debugNoDeleteCache` | Keeps temporary extraction caches for inspection. |
| `deleteEmptyTimeStamp` | Controls whether VideoSubFinder timestamps with empty OCR text are kept. |

## Typo map schema

A typo map is a JSON object of string pattern to string replacement:

```json
{
  "Iife": "life",
  "l'm": "I'm",
  "channel logo text": ""
}
```

Patterns are compiled as case-insensitive regular expressions. Escape regex
metacharacters when matching literal punctuation.
