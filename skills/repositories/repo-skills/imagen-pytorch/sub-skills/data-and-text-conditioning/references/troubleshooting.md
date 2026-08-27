# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty folder or zero samples | No files matched the recursive lowercase extension glob, or the extension list is wrong | Use the source defaults `jpg`, `jpeg`, `png`, `tiff`, normalize filename case, or point at the right folder |
| Read failure or corrupt-image error | PIL could not open or decode a file | Remove or repair the file before training |
| Wrong color channels or alpha loss | The input mode does not match the requested `channels` or `convert_image_to_type` | Convert to `L`, `LA`, `RGB`, or `RGBA` before training and keep the collator channel mode aligned |
| HF collator returns `None` | Every row in the batch failed to load, convert, or encode | Inspect the row schema, remove bad URLs or images, and avoid batches where all examples can fail together |
| URL rows are flaky or slow | The collator downloads with a short timeout and swallows fetch errors | Pre-download assets, use local images, or filter broken URLs before batching |
| Non-PIL HF image label | The image value does not support `.convert(...)` | Convert the dataset item to a PIL image first, or change the preprocessing pipeline |
| Missing T5 cache or no network | The first text-encoding call needs tokenizer or encoder assets | Warm the cache in advance, keep network available, or bypass T5 with precomputed `text_embeds` and `text_masks` |
| Caption count mismatch | Raw text paths require one caption per image | Ensure `len(texts) == batch_size` before calling the model |
| Embedding dimension mismatch | `text_embeds.shape[-1]` does not match the model’s `text_embed_dim` | Regenerate embeddings with the correct encoder size or reconfigure the model |
| Text too long | Captions are truncated at 256 tokens | Shorten the caption or accept the truncation and verify it is harmless |

## Debugging priority
1. Check the folder or row schema first.
2. Check image decode and channel mode second.
3. Check text shape and length third.
4. If the batch still fails, switch to precomputed text embeddings and isolate the text path from the image path.
