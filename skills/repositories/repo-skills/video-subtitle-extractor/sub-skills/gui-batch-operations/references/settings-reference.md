# GUI Settings Reference

## Basic settings

- Interface language.
- Subtitle language.
- Recognition mode: Auto, Fast, Accurate.
- Hardware acceleration toggle.
- Generate TXT subtitles.
- Word segmentation.

## Advanced settings

- Recognition batch count and maximum DB batch size.
- Subtitle area hint: lower part, upper part, or full screen.
- Frame extraction frequency.
- X/Y tolerance pixels and subtitle-area deviation.
- Watermark area count.
- Text similarity threshold.
- Drop score / OCR confidence threshold.
- Save directory.
- Check update on startup.

## VideoSubFinder settings

- CPU core count; `0` means automatic.
- Decoder: OpenCV by default; switch to FFmpeg for compatibility if OpenCV
  fails, with possible timeline shift.

## Development/debug settings

- Output OCR-loss frames for selected CJK languages.
- Keep cache data.
- Delete empty timestamps.
