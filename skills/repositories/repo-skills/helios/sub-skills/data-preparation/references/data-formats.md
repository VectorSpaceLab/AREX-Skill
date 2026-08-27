# Helios data formats

## Toy metadata JSON

Each item in the toy metadata file uses the same shape:

- `cut`: two integers describing the kept frame window.
- `crop`: four integers describing the crop box.
- `fps`: frames per second.
- `num_frames`: frame count for the clip.
- `resolution.height` and `resolution.width`: the target size.
- `cap`: a list of one or more caption strings.
- `path`: the relative video file path.

## Prompt list text files

A prompt list is one non-empty prompt per line. The prompt-embedding helper
uses the file stem plus a zero-padded index to create its output file names.

## Short-latent `.pt` files

The source preprocessing code saves dictionaries with keys similar to:

- `vae_latent`
- `prompt_embed`
- `first_frames_image`
- `prompt_raw`

The generated file name encodes the clip identifier, frame count, height, and
width.

## Prompt-embedding `.pt` files

Prompt-embedding artifacts store:

- `prompt_raw`
- `prompt_embed`

These are the safest artifacts to validate with a small fixture before a large
GPU preprocessing run.
