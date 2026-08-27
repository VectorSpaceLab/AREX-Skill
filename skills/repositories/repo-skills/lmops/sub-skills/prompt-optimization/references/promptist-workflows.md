# Promptist Workflows

Promptist rewrites plain text into text-to-image prompts preferred by an image-generation model, and also documents a heavier reinforcement-learning training path. In this sub-skill, Promptist support is split into safe offline planning and optional, user-approved execution. The bundled skeleton validates arguments and prints steps; it does not load models, download weights, generate images, or train.

```bash
python scripts/promptist_rewrite_skeleton.py \
  --plain-text "A rabbit is wearing a space suit" \
  --model-id microsoft/Promptist \
  --tokenizer-id gpt2 \
  --num-beams 8 \
  --num-return-sequences 8 \
  --max-new-tokens 75
```

## Pretrained local rewrite demo

Distilled rewrite flow:

1. Load a causal language model checkpoint such as `microsoft/Promptist` and tokenizer `gpt2` only after model-loading/network consent.
2. Set `tokenizer.pad_token = tokenizer.eos_token` and `tokenizer.padding_side = "left"`.
3. Strip the user's input and append the literal suffix ` Rephrase:`.
4. Generate deterministically by default with `do_sample=False`, `max_new_tokens=75`, `num_beams=8`, `num_return_sequences=8`, `eos_token_id` and `pad_token_id` set to `tokenizer.eos_token_id`, and `length_penalty=-1.0`.
5. Decode generated sequences, take the first candidate in the simple demo path, remove the original `plain_text + " Rephrase:"` prefix, and strip whitespace.
6. Treat the result as the optimized text-to-image prompt for a separate image-generation workflow.

Operational notes:

- A real local rewrite run requires PyTorch and Transformers. If model files are not already cached, loading can contact a model registry.
- GPU is recommended for responsive local rewriting. CPU can work for a simple demo but should be expected to be slow.
- The public online demo used CPU and is useful as a behavior reference, not as proof that local execution is fast or verified.
- The bundled skeleton is the safe preflight path when the user wants to plan without accidental downloads.

## Rewrite input checks

For each input prompt:

- Keep it nonempty after stripping whitespace.
- Do not append `Rephrase:` yourself unless you intentionally want that token sequence in the base text; the demo appends ` Rephrase:` internally.
- Decide whether to rewrite one prompt or a file with one prompt per nonempty line.
- Record model and tokenizer identifiers, generation limits, cache/network permission, and CPU/GPU expectations before a real run.
- For deterministic beam generation, keep `num_return_sequences <= num_beams`.

## RL training setup

Promptist reinforcement-learning training is optional and unverified at skill-creation time. Treat it as a substantial image-generation RL job rather than a smoke test.

Distilled training entrypoint arguments:

| Argument | Meaning |
| --- | --- |
| `--data` | Directory containing Promptist prompt text files. |
| `--sdmodel_name` | Stable Diffusion model identifier used by the reward scorer; the reference concept is Stable Diffusion v1.4. |
| `--gpt_path` | Supervised-finetuned prompter checkpoint used as the initial RL model. |
| `--trl_config` | PPO/TRL YAML configuration. |
| `--checkpoint_dir` | Directory for RL checkpoints. |
| `--ckpt_path` | Optional existing checkpoint to resume from. |
| `--eval_data_name` | Validation filename stem; default concept is `sentence_mix_valid`. |
| `--max_new_tokens` | Optional override for generation length in the PPO config. |

Dataset expectations from the trainer:

- Training file: `filtered_mix_train.txt` under the data directory.
- Validation file: `<eval_data_name>.txt` under the data directory.
- Each line is a plain text prompt. The loader appends ` Rephrase:` before passing prompts to the prompter.
- The reward function splits generated samples around ` Rephrase:` to recover plain text and rewritten diffuser prompts.

Reward/scoring constraints:

- The reward scorer constructs a Stable Diffusion pipeline, a DPM solver scheduler, CLIP ViT-L/14 image/text scoring, and an aesthetic MLP scorer.
- CUDA devices are addressed through `LOCAL_RANK`; distributed launches must set rank environment variables correctly.
- Stable Diffusion, CLIP, and aesthetic assets can require network access, local cache availability, GPU memory, and model-license/token approval.
- Reward computation includes image generation, so throughput is dominated by diffusion inference and GPU memory.

Distributed launch constraints:

- Training is built around an Accelerate multi-GPU launch with machine rank, main process address/port, number of machines, and total processes.
- The documented scale includes a large multi-node concept for an A100-oriented PPO config. Treat that as a scale signal, not a cheap default.
- W&B and Hugging Face credentials may be needed depending on logging, model access, and dataset staging.
- Do not claim Promptist RL training is verified unless the user-provided environment completes a bounded run.

## Route boundaries

- If the user asks to select in-context demonstrations or retrieved prompt examples, route to `../example-retrieval/SKILL.md`.
- If the user asks to turn raw domain or instruction corpora into data before Promptist/ProTeGi, route to `../adaptation-and-training/SKILL.md`.
- If the user only needs a rewrite plan, use `scripts/promptist_rewrite_skeleton.py` and stop before model loading unless they approve a real model run.
