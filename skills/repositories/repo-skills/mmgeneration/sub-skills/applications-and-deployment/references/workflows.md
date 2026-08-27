# Applications and Deployment Workflows

## Purpose

Use this reference when the task involves latent-space editing, projection, interpolation, SeFa, StyleCLIP, or TorchServe packaging.

## StyleGAN-space helpers

These workflows assume a StyleGAN-family generator with a compatible latent interface.
Common user questions include:

- How to interpolate between two latent codes.
- How to project a real image into latent space.
- How to edit latents using a CLIP or identity signal.
- How to compute closed-form factors or traverse semantic directions.

Typical expectations:

- The checkpoint should expose a StyleGAN-like generator, often with `w` or `w+` latent support.
- Projection and interpolation helpers often need a fixed seed, a source image, and an output directory.
- Editing helpers often consume a text prompt and may also use an optional identity loss.
- Most helpers are expensive enough that they should be treated as expert workflows rather than quick smoke tests.

## StyleCLIP workflow

The StyleCLIP script combines:

- a pretrained generator loaded through `init_model`,
- CLIP text tokenization,
- a latent optimization loop,
- optional editing vs free generation mode,
- an optional projected-latent warm start.

Important notes:

- It expects the `clip` package to be installed.
- It uses CUDA-oriented tensor paths and is not a good CPU-only smoke check.
- The script can initialize from a projected latent file created by the projection helper.
- The latent edit mode adds an L2 regularizer and an optional identity term.

## TorchServe packaging workflow

The TorchServe path has three pieces:

1. A packager that creates a `.mar` archive from a config and checkpoint.
2. A handler that loads the archive, restores the model, and performs inference.
3. A small client that sends requests to a running TorchServe endpoint and saves image bytes.

Important notes:

- Packaging requires `torch-model-archiver`.
- The handler is written for unconditional generation and converts the output tensor to image bytes.
- The client can request `ema`, `orig`, or both branches and then stitch results together.
- End-to-end serving requires an external TorchServe process; bundling the archive alone is not the full deployment story.

## Safe usage pattern

When you only need guidance, prefer this order:

1. Identify the model family and latent-space assumption.
2. Check whether the checkpoint is StyleGAN-like or unconditional only.
3. Confirm optional dependencies such as `clip` or TorchServe tooling.
4. Choose the lowest-risk path: help, command planning, or tiny dry-run before any expensive edit/projection job.

## Cross-links

- For the public sampling APIs that feed projection or editing, read `../../references/api-reference.md` and `../../references/model-overview.md`.
- For package install and backend compatibility, read `../../references/installation-and-compatibility.md`.
- For command shapes and deployment flag conventions, read `../../references/cli-reference.md`.
