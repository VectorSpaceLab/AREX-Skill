---
name: "generation"
description: "Routes GPT2-Chinese prompt-based text generation and batch sample export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Generation

Use this sub-skill when the task is about generating text from a checkpoint with `generate.py` or `generate_texts.py`.

## Read first

- `../references/workflows.md` for the end-to-end generation flow.
- `../references/cli-reference.md` for the exact flags and output paths.
- `../references/model-overview.md` when you need to match a checkpoint to a vocabulary bundle.
- `../references/troubleshooting.md` and this sub-skill's troubleshooting file for loop, prompt, and sample-saving issues.
- `../../scripts/check_install.py` when you want to confirm the environment can instantiate the model and sample a token sequence.

## What belongs here

- Prompted generation from a checkpoint directory.
- `generate.py` for interactive or single-prompt generation.
- `generate_texts.py` for batch generation by title list.
- Sampling controls such as `--prefix`, `--length`, `--temperature`, `--topk`, `--topp`, and `--repetition_penalty`.
- Sample saving via `--save_samples` or `--save_path`.

## What does not belong here

- Corpus preprocessing and checkpoint creation belong in training.
- Tokenizer or vocabulary creation belongs in tokenization.
- Generic sampling theory without this repo's CLI behavior belongs elsewhere.

## How to route a generation request

1. Pick the output shape.
   - One prompt, one stream of text: use `generate.py`.
   - Multiple titles or articles on disk: use `generate_texts.py`.
2. Choose the checkpoint and vocab pair.
   - `model_path` or `model_path` should point at a saved checkpoint directory.
   - `tokenizer_path` must match the config and checkpoint vocab size.
3. Choose the prompt form.
   - The usual checkpoints expect a `[CLS]`-prefixed prompt.
   - The prompt is tokenized before sampling, so keep the tokenizer mode in mind.
4. Choose the decoding behavior.
   - `--fast_pattern` is the preferred smoke path.
   - `--topk`, `--topp`, and `--temperature` shape the sampling distribution.
5. Choose the save target.
   - `--save_samples` writes a `samples.txt` file.
   - `generate_texts.py` writes one text file per generated article.

## Common decision points

- If the user wants a quick demo, keep `--batch_size 1` and use a short length.
- If the user wants file-based batch output, use the title list interface instead of copy-pasting one prompt at a time.
- If the user is asking why the same sample repeats, check `nsamples` versus `batch_size` first.
- If the task is really about tokenization quality or vocabulary choice, route back to the tokenization sub-skill.

## Output expectations

- Printed samples on stdout for the interactive path.
- `samples.txt` when `--save_samples` is used.
- `<title-index>-<article-index>.txt` files when `generate_texts.py` is used.
