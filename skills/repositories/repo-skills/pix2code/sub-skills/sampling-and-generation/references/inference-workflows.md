# pix2code Inference Workflows

## Purpose

Read this for the command patterns behind screenshot-to-DSL generation.

## Single-image generation

The historical single-image workflow accepts four required arguments plus an optional search mode: artifact directory, model name, image path, and output path. The optional fifth argument selects greedy decoding or a beam width integer. The bundled checker helps confirm that the artifact directory is complete before you adapt those arguments to the current checkout or your own wrapper.

## Batch generation

The historical batch workflow scans an input directory for `.png` files, generates one `.gui` file per image, and strips `<START>` / `<END>` before writing the result. It uses the same artifact-directory and search-mode conventions as single-image generation.

## Runtime assumptions

- `meta_dataset.npy` must be readable and match the trained model.
- `words.vocab` must exist in the artifact directory.
- `model/classes/Sampler.py` loads the vocabulary and performs greedy or beam-search decoding.
- `Utils.get_preprocessed_img` resizes each screenshot to `IMAGE_SIZE = 256` and normalizes pixel values.

## Recommended order

1. Validate the artifact directory.
2. Validate the screenshot input.
3. Choose greedy or beam search.
4. Inspect the generated `.gui` output before compiling it into platform code.
