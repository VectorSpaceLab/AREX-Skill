# Intended Use and License Caveats

This reference collects the repository's public statements about how Alpaca data may be used. It is not legal advice.

## What the repo says

| Source | Statement |
| --- | --- |
| `README.md` | Alpaca is intended and licensed for research use only. The dataset is CC BY-NC 4.0. Models trained using the dataset should not be used outside of research purposes. |
| `DATA_LICENSE` | The dataset is licensed under Creative Commons Attribution-NonCommercial 4.0 International. |
| `datasheet.md` | The dataset should not be used for commercial usage that competes with OpenAI. |
| `model_card.md` | Primary intended use is research on instruction-following LLMs; out-of-scope uses include production systems and competing with the OpenAI API. |
| `LICENSE` | Code is Apache 2.0. |
| `WEIGHT_DIFF_LICENSE` | Weight-diff artifacts are CC BY-NC 4.0. |
| `model_card.md` | The model card text also says code and data are Apache 2.0, which conflicts with the dedicated data license files and README badge. |

## Practical guidance for this sub-skill

- Treat the dataset as a research-oriented artifact.
- Treat commercial use as out of scope unless a project owner or legal reviewer has explicitly resolved the data-license conflict.
- Do not present Alpaca as suitable for production use or as a safety-finetuned model.
- Do not bundle or redistribute the released dataset inside the skill tree.
- Do not imply that a clean prompt render, a passing validator, or a training example makes a downstream use case permitted; use and licensing are separate decisions.

## Recommended interpretation when users ask for a quick answer

If the user only wants an operational answer, say:

- The code is Apache 2.0.
- The released data and weight-diff artifacts are described as CC BY-NC 4.0 in the repository's dedicated license files and README.
- The datasheet and model card also contain conflicting wording, so any non-research or commercial plan should be reviewed against the repository's dedicated license files and project policy before use.

## Common caveats

- The dataset was generated using OpenAI API outputs.
- The repo text repeatedly discourages production deployment and competing commercial use.
- The release is about a training dataset and a research model, not a safety-certified or policy-approved system.
- If you are about to fine-tune, validate the file schema and prompt formatting first, then hand off to `fine-tuning`.
- If you are about to generate more instructions, hand off to `instruction-generation` and respect the OpenAI/API restrictions separately.
