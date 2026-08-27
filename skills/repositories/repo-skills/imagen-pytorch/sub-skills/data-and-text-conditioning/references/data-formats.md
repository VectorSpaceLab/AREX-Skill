# Data formats

## Local image folders
`Dataset(folder, image_size, exts, convert_image_to_type=None)` recursively globs the folder for the listed lowercase extensions. The source defaults are `jpg`, `jpeg`, `png`, and `tiff`.

Each item:
- opens one file with PIL
- optionally converts image mode with `convert_image_to_type`
- resizes, random-flips, center-crops, and converts to a tensor

`get_images_dataloader(...)` wraps that dataset and returns image-only batches shaped like:

- `[batch, channels, image_size, image_size]`

Useful kwargs:
- `shuffle`: whether to shuffle the dataset
- `cycle_dl`: whether to wrap the loader in an infinite cycle
- `pin_memory`: whether to enable pinned-memory loading

## Hugging Face row schema
`Collator(image_size, url_label, text_label, image_label, name, channels)` expects one of two row shapes:

| Path | Required row fields | Result |
| --- | --- | --- |
| URL path | `url_label`, `text_label` | Downloads the image, converts it to the requested channel mode, encodes text with T5, and returns a 2-tuple of `(images, encoded_texts)` |
| Local image path | `image_label`, `text_label` | Uses the row image object directly, converts it to the requested channel mode, encodes text with T5, and returns a 2-tuple of `(images, encoded_texts)` |

Notes:
- The image object must support `.convert(...)` like a PIL image.
- The text value must be a string or string-like label accepted by T5 tokenization.
- The collator does not emit `text_masks`; it only returns image tensors and encoded text tensors.
- If every row in a batch fails, the collator returns `None`.

## Dataloader tuple order
`ImagenTrainer.step_with_dl_iter(...)` maps the dataloader tuple onto keyword names in order.

Default keyword order:
1. `images`
2. `text_embeds`
3. `text_masks`
4. `cond_images`

Implications:
- A one-item loader feeds only `images`.
- A two-item loader feeds `images` and `text_embeds`.
- A three-item loader feeds `images`, `text_embeds`, and `text_masks`.
- A four-item loader feeds `images`, `text_embeds`, `text_masks`, and `cond_images`.
- If you need a different layout, override `dl_tuple_output_keywords_names` to match your batch tuple exactly.

## Channel modes
The collator and dataset path rely on PIL mode conversion. The practical channel targets are:
- `L`
- `LA`
- `RGB`
- `RGBA`
