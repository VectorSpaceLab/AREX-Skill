# Training data formats

## Single-concept runs

A single-concept launch uses these values:

- `instance_data_dir`
- `instance_prompt`
- `class_data_dir` when prior preservation is enabled
- `class_prompt` when prior preservation is enabled

## Multi-concept runs

A multi-concept launch uses `concepts_list`, which is a JSON list of concept objects. Each object needs the same fields as the single-concept route.

The bundled example in `assets/concept_list.json` shows a two-concept manifest with separate instance and class directories.

## Prior preservation behavior

- Generated prior uses a class-image directory and a class prompt string.
- Real prior rewrites the class fields to the bundle layout used by the data-preparation route.
- The training dataset loader uses the class list files when the real-prior route is active.

## Image preprocessing

The dataset pipeline performs the following steps:

- resize to the chosen resolution
- center crop or random crop
- optional horizontal flip
- tokenization of the instance and class prompts

SDXL adds crop-coordinate ids and a dual text-encoder path.

## Modifier-token rules

- `--modifier_token` and `--initializer_token` are split on `+`.
- Every modifier token needs a matching initializer token.
- The initializer token must be a single token in the target tokenizer.
- The tokenizer must not already contain the modifier token.
