# Data formats

## Concept manifests

Custom Diffusion training consumes a JSON list of concept objects. Each object needs these fields:

- `instance_prompt`
- `class_prompt`
- `instance_data_dir`
- `class_data_dir`

The bundled `assets/concept_list.json` is a compact example. It shows the multi-concept layout used by the README and the diffusers training scripts.

## Instance data

`instance_data_dir` points to a directory of instance images for one concept.

Notes:

- The training dataset loader iterates files in this directory.
- Use a real directory on disk, not a prompt string.
- Image preprocessing later resizes and crops the files to the chosen training resolution.

## Prior-preservation layouts

Custom Diffusion supports two class-data styles:

### Generated prior

- `class_data_dir` is a directory of class images.
- `class_prompt` is a prompt string used to generate or describe those images.

### Real prior / offline prior bundle

- `class_data_dir` points to an `images.txt` file that lists the class-image paths.
- `class_prompt` points to a `caption.txt` file with one caption per image.
- `urls.txt` is optional provenance for the retrieved images.

The layout helper validates all three pieces together so you can catch mismatches before training.

## File-order rules

- Keep the image list, caption list, and URL list in the same order.
- Do not leave blank lines in the caption file.
- The number of caption lines should match the number of image paths.
- The number of image list entries should match the number of images the training run expects.

## Accepted image extensions

The validator treats common raster formats as images:

- `.jpg` / `.jpeg`
- `.png`
- `.webp`
- `.bmp`

## What training does with these fields

During a real-prior run, the training route rewrites the concept fields so the class prompt becomes the caption file and the class data directory becomes the image-list file.
