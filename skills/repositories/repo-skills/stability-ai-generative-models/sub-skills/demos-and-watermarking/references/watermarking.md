# Watermarking Reference

The repository embeds and detects a fixed invisible watermark in generated image outputs. This reference separates detection math from heavyweight image decoding so future agents can reason about classifications safely.

## Fixed Message

The watermark is a fixed 48-bit message chosen at random in the repository:

```text
WATERMARK_MESSAGE = 0b101100111110110010010000011110111011000110011110
```

Both the embedder and detector derive `WATERMARK_BITS` from this message. The bit length is 48.

## Embedding Behavior

Watermark embedding appears in `sgm/inference/helpers.py` and is also imported by Streamlit/Gradio helpers.

Key behavior:

- `WatermarkEmbedder` wraps `imwatermark.WatermarkEncoder`.
- `encoder.set_watermark("bits", WATERMARK_BITS)` sets the fixed 48-bit payload.
- Input tensors are expected in RGB channel-first form, with values in `[0, 1]` and shape `[B, C, H, W]` or `[N, B, C, H, W]`.
- The embedder converts tensors to uint-like image arrays, flips RGB to BGR for the watermark library, encodes with method `dwtDct`, converts back to RGB tensor layout, and clamps to `[0, 1]`.
- `perform_save_locally()` embeds the watermark before saving images from demo/API-style helpers.
- Gradio SVD output also embeds watermark bits before filtering and MP4 writing.

## Detection Behavior

`scripts/demo/detect.py` decodes image files using `cv2` plus `imwatermark` or a minimal `imwatermark.maxDct` fallback. Detection is not dependency-light; classification of already-decoded bit counts is dependency-light.

Input expectations for full detection:

- Images are read with `cv2.imread`, so the detector receives BGR image arrays.
- Images must be large enough for `dwtDct`; the fallback raises `image too small, should be larger than 256x256` when `height * width < 256 * 256`.
- The original detector works best when the image dimensions match the dimensions at embedding time, commonly 1024x1024 or 512x512 for image demos.
- Resizing, cropping, recompression, aggressive filtering, or frame/video conversion can reduce the number of matching bits.

## Threshold Logic

The original detector counts how many of the 48 decoded bits match `WATERMARK_BITS`. It then selects the first threshold whose limit is greater than the bit count.

| Bit matches | Classification | Notes |
| --- | --- | --- |
| `<= 27` | No watermark detected | A low match count is treated as no detected watermark. |
| `28..33` | Partial watermark match. Cannot determine with certainty. | Ambiguous; do not claim provenance. |
| `34..35` | Likely watermarked | Repository note: in its 10,000-image test, 0.02% of real images were falsely detected as likely watermarked. |
| `36..48` | Very likely watermarked | Repository note: in its 10,000-image test, no real images were falsely detected as very likely watermarked. |

The detector uses a sentinel threshold of `49` for the final bucket because only 48 bits exist.

## Bundled Classifier

Use `scripts/watermark_match_thresholds.py` when bit-match counts are already available and the task is only to classify them.

```bash
python sub-skills/demos-and-watermarking/scripts/watermark_match_thresholds.py 27 28 33 34 35 36 48
python sub-skills/demos-and-watermarking/scripts/watermark_match_thresholds.py '[27, 33, 35, 48]'
```

JSON output is available for downstream tooling:

```bash
python sub-skills/demos-and-watermarking/scripts/watermark_match_thresholds.py --json '[34, 48]'
```

The helper validates that counts are integers from 0 through 48, accepts integer arguments or a JSON list, and does not import image, model, CUDA, OpenCV, or watermark libraries.

## Caveats

- Invisible watermarking is probabilistic evidence, not proof of origin.
- A watermarked image may fail detection after resizing, cropping, compression, denoising, color-space conversion, or other transformations.
- An unwatermarked image may match enough bits by chance, especially in the ambiguous or likely buckets.
- The watermark script is public; anyone can apply the same watermark to unrelated images.
- Video workflows may watermark frames before MP4 encoding, but video compression and frame handling can alter detectability.
- Do not claim a watermark is absent solely from a failed decode; distinguish unreadable images, too-small images, dependency failures, and low bit counts.
