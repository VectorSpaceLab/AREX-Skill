# Prompting Workflows

This reference covers CLIP zero-shot text prompt construction. It assumes a model and image preprocessing path are already handled by `../model-loading-inference/`.

## Class Taxonomy First

A CLIP classifier only chooses among the text candidates you provide. Before writing templates:

- Use mutually exclusive class names at a comparable level of specificity.
- Replace ambiguous labels with explicit meanings when the visual class is not obvious, such as `kite (bird of prey)` instead of `kite` when the class is not a flying toy.
- Avoid mixing objects, attributes, actions, places, and identities unless the task really requires that mixture.
- Treat top-k results as relative rankings inside the candidate set; adding or removing labels can change probabilities and bias behavior.
- Do not use sensitive demographic, crime, health, or identity categories for deployed decisions. The model card reports that performance and disparities can shift substantially with category construction, especially for people-related labels.
- Keep use English by default; CLIP was not purposefully trained or evaluated for non-English language use.

If a user provides ambiguous or unsafe categories, pause and redesign the taxonomy instead of blindly classifying.

## Template Design

The repository evidence uses templates containing `{}` as the class-name placeholder. Examples include:

- `a photo of a {}.` for generic object categories.
- `a photo of a {}, a type of bird.` for fine-grained birds.
- `a photo of a {} texture.` for texture datasets.
- `a photo of a person {}.` for action labels, only when people-related use is justified and reviewed.
- ImageNet prompt engineering used visual variants such as `a bad photo of the {}.`, `a rendering of a {}.`, `a drawing of a {}.`, `a {} in a video game.`, and `art of the {}.`

Template rules:

1. Use exactly one `{}` placeholder for standard class expansion.
2. Match articles and grammar to the label set; `a photo of a {}` can be awkward for plural labels, so use `a photo of the {}` or label-specific synonyms when needed.
3. Keep templates short enough that the expanded prompt fits CLIP's 77-token context length.
4. Prefer a small, domain-relevant template set over a huge generic set when latency or context length is a concern.
5. Dry-run tokenization before inference when class names or templates are generated automatically.

## Zero-Shot Classifier Weights

The prompt-engineering notebook builds classifier weights per class by expanding every template, encoding text, normalizing prompt embeddings, averaging them, and normalizing again.

Importable helper contract from `scripts/build_zeroshot_classifier.py`:

```python
from pathlib import Path
import torch
import clip
from build_zeroshot_classifier import build_zeroshot_classifier

model, preprocess = clip.load("ViT-B/32", device="cpu")
class_names = ["cat", "dog", "electric ray"]
templates = ["a photo of a {}.", "a blurry photo of a {}."]

with torch.no_grad():
    zeroshot_weights = build_zeroshot_classifier(model, class_names, templates, device="cpu")
```

Returned weights have shape `[text_feature_dim, num_classes]`, so a normalized image feature batch `[batch, text_feature_dim]` can be multiplied by the weights.

Core algorithm:

1. For one class, create `texts = [template.format(class_name) for template in templates]`.
2. Tokenize with `clip.tokenize(texts, context_length=77, truncate=False)`.
3. Move tokens to the same device as the model.
4. Call `model.encode_text(tokens)`.
5. Normalize each prompt embedding with `embedding / embedding.norm(dim=-1, keepdim=True)`.
6. Average prompt embeddings for the class.
7. Normalize the averaged class vector.
8. Stack all class vectors along `dim=1`.

Do not average raw, unnormalized prompt embeddings: the notebook normalizes before and after averaging.

## Scoring Images Against Text Weights

For a preprocessed image batch from `../model-loading-inference/`:

```python
with torch.no_grad():
    image_features = model.encode_image(image_inputs)
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    logits = 100.0 * image_features @ zeroshot_weights
    probs = logits.softmax(dim=-1)
    values, indices = probs.topk(5, dim=-1)
```

Interpretation guidance:

- `logits` are cosine similarities scaled by `100.0`, matching README/notebook examples.
- `softmax` probabilities are normalized only across the candidate class list.
- `topk` is often more useful than a single top-1 result when labels overlap or classes are visually similar.
- If labels include an `other` or `unknown` class, write an explicit prompt for it and validate it; CLIP does not automatically know the open set.

## Prompt Ensembling

Prompt ensembling is useful when a class can appear under varied renderings, camera quality, scale, or media style. The ImageNet notebook used 80 templates and reported a selected 7-template subset:

1. `itap of a {}.`
2. `a bad photo of the {}.`
3. `a origami {}.`
4. `a photo of the large {}.`
5. `a {} in a video game.`
6. `art of the {}.`
7. `a photo of the small {}.`

Use these as evidence that visual-style templates can help, not as a universal best set. For domain tasks, write templates that mirror the expected image source: product photos, satellite images, microscope images, diagrams, OCR renderings, textures, or actions.

## Batching Text Prompts

`clip.tokenize` accepts either a string or a list of strings and returns a padded 2-D tensor `[n, context_length]`. For many classes:

- Batch prompts per class when averaging class templates.
- Move token tensors to the model device before `model.encode_text`.
- Use `torch.no_grad()` for classifier construction unless training a separate component.
- Keep a stable class order and persist that order next to saved weights.

## Files and CLI Inputs

The helper script accepts class names and templates either directly or from text files. File format is one entry per line; blank lines and lines beginning with `#` are ignored. This keeps runtime prompt workflows self-contained and does not require source repository datasets or notebooks.
