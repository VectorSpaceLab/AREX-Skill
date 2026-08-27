# OpenFlamingo training data formats

OpenFlamingo trains with WebDataset tar shards. The two main training streams are LAION image-text pairs and MMC4 / ChatGPT-style interleaved image-text sequences.

## LAION shard format

LAION shards are tar files with paired image and text samples.

### Required sample pieces

- An image file with one of these suffixes: `.jpg`, `.jpeg`, or `.png`
- A text file with the same sample key and suffix `.txt`

### Loader expectations

The LAION loader filters out samples that do not contain both image and caption fields.
It then:

- decodes the image through the configured image processor,
- applies a random horizontal flip,
- wraps the caption as `<image>...<|endofchunk|><eos>`, and
- truncates captions to 32 tokens by default.

### Practical implications

- The tar stream should contain image and caption pairs, not image-only or text-only records.
- If the shard directory does not expose size metadata, pass `--train_num_samples_laion`.
- If you are not resampling shards, make sure the LAION shard count is large enough for the number of workers and ranks.

## MMC4 shard format

MMC4 shards are tar files where each sample is a JSON record.

### Expected JSON shape

The loader expects one of these shapes:

1. **MMC4-style interleaved samples**
   - `text_list`: list of sentence strings
   - `similarity_matrix`: image-by-sentence similarity scores
   - `image_info`: list of image records, each with `image_base64`

2. **ChatGPT-generated interleaved samples**
   - `is_gpt`: truthy marker
   - `example`: interleaved text template containing image markers
   - `image_map`: mapping from image placeholders to records that include `base64_image`

### Loader behavior

For MMC4-style samples, the loader:

- drops image records that do not contain `image_base64`,
- skips images smaller than about 10 KB,
- solves a one-to-one assignment between images and sentences using the similarity matrix,
- keeps only matches above `--mmc4_textsim_threshold`,
- truncates to `--mmc4_max_num_images`,
- zero-pads missing images, and
- tokenizes the merged text to 256 tokens by default.

It also rejects samples with too few images after filtering or truncation.

### Threshold scale note

The repo history shows two scales for `--mmc4_textsim_threshold`:

- the parser default is `30`, and
- the example training command uses `0.24`.

Use the threshold scale that matches the similarity scores produced by your MMC4 conversion pipeline.

## Sample-count and shard-count rules

When shard size metadata exists, the loader can infer dataset length from:

- `sizes.json`, or
- `__len__` in the shard directory.

When that metadata is missing, you must provide explicit sample counts with:

- `--train_num_samples_laion`
- `--train_num_samples_mmc4`

If `--dataset_resampled` is off, shard count must also satisfy:

- `num_shards >= workers * world_size`

## Suggested validation checks

Before launch, confirm that:

- every LAION shard contains paired image and caption samples,
- every MMC4 shard contains JSON records with the required keys,
- the LAION and MMC4 sample budgets yield the same number of training batches, and
- the MMC4 threshold scale matches the similarity score range in your JSON records.
