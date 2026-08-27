# Feature Workflows

CLIP's image and text encoders return unnormalized embeddings. Use this reference for feature extraction and downstream evaluation after model loading and preprocessing are already handled by [model-loading-inference](../../model-loading-inference/).

## Core Feature Pattern

- Put the model in evaluation mode and wrap extraction in `torch.no_grad()` or `torch.inference_mode()`.
- Move preprocessed image tensors or tokenized text tensors to the same device as the model.
- Call `model.encode_image(image_batch)` for image embeddings and `model.encode_text(text_tokens)` for text embeddings.
- Cast features to `float32` before exporting or comparing if the model runs in fp16 on CUDA.
- Normalize before cosine similarity: `features = features / features.norm(dim=-1, keepdim=True)`.
- Keep labels, filenames, dataset splits, class names, and model metadata with the exported features.

`model(image, text)` performs the normalization internally and returns image/text logits from cosine similarity multiplied by the learned logit scale. Direct `encode_image` and `encode_text` calls do not normalize their outputs.

## Batch Image Extraction

For image directories, prefer a deterministic DataLoader-style loop:

1. Collect image paths in sorted order with a fixed extension allowlist.
2. Open each image with PIL and convert to RGB.
3. Apply the CLIP preprocess transform returned by `clip.load`.
4. Batch tensors with `DataLoader` or a simple chunked loop.
5. Encode each batch with `model.encode_image` under inference mode.
6. Convert to CPU `float32`, optionally L2-normalize, and append to an output list.
7. Save features and path metadata to a compressed `.npz` file.

Use `scripts/extract_image_features.py` for this pattern when the input is a local image directory. It accepts a named CLIP model or local checkpoint path, an explicit device, `--download-root`, `--jit`, batch-size, output path, and `--no-normalize` for rare workflows that need raw encoder outputs.

## Text Embeddings

For text labels, captions, or retrieval queries:

- Tokenize strings with `clip.tokenize(texts, truncate=False)` unless the caller explicitly accepts truncation.
- Keep the default context length of 77 unless the loaded model and task have been verified for a different value.
- Use prompt text that matches the evaluation context; poor class wording can dominate the result.
- Normalize text embeddings before comparing with normalized image embeddings.
- Save the original text strings beside the text feature array.

Prompt template selection and ensembling are owned by [prompt-engineering](../../prompt-engineering/). This sub-skill assumes the text strings are already chosen.

## Similarity and Search Prototypes

For a small image-text or image-image retrieval prototype:

- Store normalized `float32` features in memory or `.npz` for small datasets.
- Compute cosine scores with matrix multiplication, for example `scores = image_features @ text_features.T`.
- For CLIP-style zero-shot probabilities, multiply similarities by `100.0` before `softmax`, matching the README example.
- Inspect top-k results with filenames and labels, not just scores.
- Validate the taxonomy and prompts before interpreting failures as model failures.

For large retrieval systems, `.npz` plus exact matrix multiplication is only a prototype. Move to an approximate-nearest-neighbor index, sharded arrays, or a database only after validating normalization, metadata, and responsible-use constraints on a small fixture.

## Linear-Probe Recipe

The README demonstrates a scikit-learn logistic regression probe over image features. Keep the recipe explicit and bounded:

1. Split data into train, validation, and test sets before fitting.
2. Extract image features for each split without gradient tracking.
3. Train `sklearn.linear_model.LogisticRegression` on train features.
4. Tune `C`, class weighting, solver, and maximum iterations on validation only.
5. Report final test accuracy once, with confidence intervals or per-class metrics when possible.
6. Record feature model name, prompt/taxonomy decisions, split seed, feature normalization choice, and probe hyperparameters.

A linear probe evaluates one classifier on top of CLIP features; it is not evidence that a deployed CLIP system is safe or robust. The model card notes that linear probes can underestimate model performance, and class taxonomy choices can also change outcomes.

## Storage Outputs

For `.npz` feature archives, include at least:

- `features`: `float32` array shaped `[n_items, feature_dim]`.
- `paths` or `ids`: string/object array aligned with `features`.
- `normalized`: boolean flag encoded as a scalar array.
- `model`: the model name or local checkpoint basename supplied by the user.
- `device`: the effective extraction device.

Optional arrays include labels, split names, image sizes, failure paths, prompt texts, and extraction options. Avoid absolute source-checkout paths in public examples; user data paths in generated outputs are runtime artifacts, not bundled skill content.

## Validation Checks

Before trusting evaluation results, verify:

- `features.shape[0]` matches the number of successfully processed items.
- No rows contain NaN or infinite values.
- Normalized features have norms close to 1.0 when cosine similarity is used.
- Path/id metadata order matches the feature row order.
- A tiny fixture produces stable top-k neighbors after saving and reloading the `.npz` file.
- Batch size changes do not materially alter extracted features beyond expected floating-point tolerance.
- Text/image features are from the same CLIP checkpoint and preprocessing pipeline.

For offline environments, use a local checkpoint path or a pre-populated CLIP cache and avoid dataset downloads.
