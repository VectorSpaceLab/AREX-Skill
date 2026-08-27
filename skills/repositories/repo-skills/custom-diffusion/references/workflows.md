# Custom Diffusion workflows

This skill is split into five routes. Start with the route that matches the request, then use the bundled validator or helper script before a long or expensive run.

## 1. Prepare concept data

Use `sub-skills/data-preparation/` when you need local instance images, generated prior-preservation images, or real-prior bundles.

Typical flow:

1. Collect instance images for each concept.
2. Decide whether the class data will be generated locally or reused from a real-prior bundle.
3. Validate the layout with `sub-skills/data-preparation/scripts/validate_regularization_layout.py`.
4. If you are using a JSON concept manifest, validate it with `scripts/validate_concepts.py`.
5. Hand the concept manifest to the training route.

Real-prior retrieval is network-sensitive and intentionally reference-only. Prefer a local bundle when the environment must stay offline.

## 2. Train a model

Use `sub-skills/training/` for the diffusers training CLIs, including the SDXL branch.

Typical flow:

1. Validate the concept manifest and training inputs.
2. Choose single-concept or multi-concept mode.
3. Choose `--freeze_model crossattn_kv` for the default K/V-only update or `--freeze_model crossattn` for full cross-attention updates.
4. Decide whether prior preservation uses generated class images or a real-prior bundle.
5. Decide whether to train the text encoder or use modifier tokens.
6. Launch `accelerate` only after the layout and backend checks pass.
7. Expect a `delta.bin` output in the training output directory.

## 3. Sample from a delta checkpoint

Use `sub-skills/inference/` when you already have a delta checkpoint and need image generation.

Typical flow:

1. Confirm the delta layout with `sub-skills/checkpoint-tools/scripts/check_delta_layout.py`.
2. Decide whether the checkpoint is compressed.
3. Use a single prompt or a prompt file.
4. Keep the seed, guidance scale, and step count aligned with the source contract.
5. Expect both a prompt montage and per-sample images under the delta directory.

## 4. Extract, compress, or compose deltas

Use `sub-skills/checkpoint-tools/` when you need legacy delta extraction, SVD-based compression, or diffusers-side composition of multiple concepts.

Typical flow:

1. Extract the K/V deltas from checkpoint folders when working from legacy checkpoints.
2. Compress a delta only after you know whether the sampler expects compressed or uncompressed weights.
3. Validate the layout after extraction or compression.
4. Route composed outputs back to inference.

The delta extraction route is the only CPU-substitutable capability in the selected scope; the other delta workflows need CUDA and local weights.

## 5. Evaluate generated samples

Use `sub-skills/benchmarking/` for CustomConcept101 evaluation.

Typical flow:

1. Validate the sample folder layout before any expensive CLIP/DINO work.
2. Keep `samples/` PNG-only and `prompts.json` aligned with the file stems.
3. Provide the `+`-separated target image paths in the order you want the metric suffixes to appear.
4. Expect the evaluator to update a pandas pickle keyed by the sample root.

## Cross-route handoffs

- `data-preparation` feeds `training`.
- `training` feeds `inference` and `checkpoint-tools`.
- `checkpoint-tools` feeds `inference`.
- `inference` feeds `benchmarking`.

When a request spans multiple routes, use the first route that can make the inputs valid, then move downstream.
