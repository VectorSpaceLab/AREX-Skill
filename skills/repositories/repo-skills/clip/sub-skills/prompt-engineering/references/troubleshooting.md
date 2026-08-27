# Troubleshooting Prompt Engineering

## `RuntimeError: Input ... is too long for context length 77`

Cause: an expanded prompt exceeds CLIP's fixed text context length, including start/end tokens.

Fix:

- Dry-run tokenization with `truncate=False` to identify the exact class/template pair.
- Shorten templates before shortening labels; keep the class identity clear.
- Replace verbose labels with concise names plus short parenthetical disambiguators.
- Use `truncate=True` only when you intentionally accept losing tail tokens and confirm the class words remain in the prompt.
- Avoid generated paragraphs, URLs, long metadata strings, and multi-label descriptions as class names.

## Malformed Template Strings

Symptoms:

- `IndexError`, `KeyError`, or formatting errors from `template.format(class_name)`.
- Prompts literally contain `{}` because the template was not formatted.
- Templates add multiple class names unexpectedly.

Fix:

- For standard class prompts, require exactly one `{}` placeholder.
- Escape literal braces as `{{` and `}}` if a template needs visible braces.
- Keep templates in a plain one-template-per-line file and inspect the expanded prompt list before model calls.
- Use the helper script's `--dry-run-tokenize` mode to catch formatting and tokenization problems without loading a model.

## Poor or Ambiguous Class Taxonomy

Symptoms:

- Top-k predictions look plausible but unstable.
- Similar classes compete unexpectedly.
- Probabilities change dramatically when unrelated classes are added or removed.

Fix:

- Make classes mutually exclusive and visually grounded.
- Add disambiguators for overloaded words, such as `crane bird` versus `construction crane`.
- Keep all labels at a similar granularity.
- Add an explicit `other` or `none of these` candidate only after validating its behavior.
- Report top-k results and the candidate list, not only top-1.

## Unsafe or Bias-Prone Categories

Symptoms:

- The class list includes sensitive demographics, crime labels, surveillance-style categories, identity inference, or denigration-prone labels.
- The user asks for deployed people classification without task-specific validation.

Fix:

- Warn that CLIP's model card says performance and bias can depend strongly on class construction.
- Refuse or redesign categories for surveillance, facial recognition, denigration, or high-impact decisions.
- For research audits, document the fixed taxonomy, dataset, consent/licensing assumptions, and subgroup analysis plan.
- Prefer non-sensitive, task-relevant visual categories when possible.

## Prompt Batching and Device Mistakes

Symptoms:

- `Expected all tensors to be on the same device`.
- `model.encode_text` receives strings instead of token tensors.
- CUDA-specific code fails on CPU-only machines.

Fix:

- Tokenize first, then move tokens with `.to(device)`.
- Avoid hard-coded `.cuda()` in portable helpers.
- Put model and token tensors on the same device.
- Wrap classifier construction in `torch.no_grad()`.
- Keep class-name order next to returned weight columns.

## Unnormalized Text Features

Symptoms:

- Scores differ from README/notebook examples.
- Prompt ensembling is dominated by magnitude rather than direction.
- Image-feature dot products are not cosine-like.

Fix:

- Normalize every prompt embedding before averaging templates for a class.
- Normalize the averaged class embedding before stacking classifier weights.
- Normalize image features before multiplying by `zeroshot_weights`.
- Use `100.0 * image_features @ zeroshot_weights` for README/notebook-style logits.

## Multilingual or Non-English Prompts

Symptoms:

- Results degrade unexpectedly for non-English labels.
- Translated class names underperform English equivalents.

Fix:

- Prefer English labels/templates by default.
- If multilingual use is necessary, validate against task-specific examples and avoid treating scores as calibrated.
- Consider adding English aliases or using an implementation designed for multilingual CLIP-like models.

## Low Confidence or Flat Top-K Scores

Cause: the image may be out of distribution, class names may not match visible content, or the candidate set may omit the right answer.

Fix:

- Inspect top-k labels and raw logits.
- Try domain-specific templates that match the image source.
- Add missing plausible classes or remove irrelevant distractors.
- Revisit image preprocessing in `../model-loading-inference/` if all scores look wrong.
- Do not convert flat scores into confident real-world decisions.
