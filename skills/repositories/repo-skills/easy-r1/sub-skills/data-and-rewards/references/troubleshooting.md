# Data and reward troubleshooting

Use this guide when an EasyR1 data/reward task fails before or during rollout. It focuses on dataset rows, prompt rendering, media handling, reward imports, score dictionaries, and backend limitations.

## Fast triage

1. Run the deterministic contract smoke:

   ```bash
   python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py
   ```

2. For a custom reward, validate the exact target and kwargs:

   ```bash
   python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py \
     --target ./my_reward.py:compute_score \
     --mode batch \
     --kwargs-json '{}'
   ```

3. Inspect a few serialized dataset rows before launching training. Confirm the prompt column, answer column, media columns, and placeholder counts.
4. If the failure mentions Ray, vLLM, CUDA memory, FSDP, or distributed startup, route to `training-workflows`; this sub-skill can only validate data/reward contracts.

## Dataset and prompt issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Prompt construction filters out many rows. | `data.filter_overlong_prompts=true` and rendered prompts exceed `data.max_prompt_length`. | Increase `data.max_prompt_length`, shorten the prompt template, reduce `data.max_pixels`, or disable filtering only if truncation behavior is intentional. |
| `Prompt length ... is longer than ...`. | Truncation mode is `error` and the rendered prompt is too long. | Increase max length or choose left/right truncation intentionally; do not silently truncate reasoning-critical context. |
| `Image features and image tokens do not match`. | Image placeholder count, media list length, or pixel/token budget does not match the processor output. | Ensure one `<image>` per image item, set `data.max_prompt_length` high enough, and reduce `data.max_pixels` if vision tokens are too large. |
| Image file not found or PIL cannot open image. | Relative image path is not rooted correctly, or the file is corrupt/unsupported. | Set `data.image_dir` to the media root used by the training process; verify image files can be opened before training. |
| Video fetch fails. | Video path, codec, FPS extraction, or vision utility dependencies are unavailable. | Verify video files independently, keep FPS modest, and remember this version uses the media-root key `data.image_dir` for relative video strings. |
| Mixed text/image dataset fails only on text rows. | Text rows omit the image column or include `<image>` while `images` is empty. | Keep `images: []` for text-only rows when the dataset schema has an image column, and remove `<image>` from those prompts. |
| Multimodal text loses normal text around placeholders. | Placeholder splitting creates alternating text and media chunks; empty chunks are skipped. | Write prompts as clear text around `<image>` or `<video>` placeholders and inspect rendered prompts on a small sample. |
| Jinja template error. | Template syntax uses undefined variables or invalid filters. | Use `{{ content | trim }}` as the main variable. Keep advanced Jinja logic out of prompt templates unless it is tested independently. |
| Rendered prompt contains literal `\n` instead of new lines. | Template text or CLI override double-escaped newlines. | Store the template in a file and use real line breaks; avoid shell-escaped prompt bodies. |
| Remote dataset loading hangs or fails. | Dataset identifier requires network, authentication, or uncached files. | Use local dataset files for deterministic checks; only allow remote loading when network/cache policy is explicit. |

## Reward import and metadata issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Reward function is not provided.` | `worker.reward.reward_function` is null or omitted. | Set a target path with optional function suffix, for example `./my_reward.py:compute_score`. |
| Reward file not found. | The path is resolved from the training process working directory and does not exist there. | Use an absolute path or run training from the directory that contains the reward module. Keep generated skill docs free of machine-specific paths. |
| `Module ... does not have function ...`. | The suffix after `:` is wrong, or no suffix was provided and the module has no `main`. | Rename the function or configure the correct suffix. Validate with the smoke script. |
| Import fails before scoring. | The reward module imports unavailable dependencies or performs side effects at import time. | Move heavyweight setup into the function body only when needed, install required packages, or keep the reward pure-Python. |
| `Unsupported reward type`. | `REWARD_TYPE` is not `batch` or `sequential`. | Set `REWARD_TYPE = "batch"` for list-in/list-out functions or `"sequential"` for dict-in/dict-out functions. |
| Batch reward receives a list but code expects a dict. | Function body is sequential while metadata/default mode is batch. | Either change `REWARD_TYPE` to `sequential` or rewrite the function to iterate over `reward_inputs`. |
| Sequential reward receives a dict but code expects a list. | Metadata says sequential but the function was written as batch. | Set `REWARD_TYPE = "batch"` or adapt the function signature. |
| DAPO reward errors on missing kwargs. | Required kwargs such as `max_response_length`, `overlong_buffer_length`, or `overlong_penalty_factor` were not supplied. | Pass them in `worker.reward.reward_function_kwargs` and validate with `--kwargs-json`. |

## Score dictionary issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'overall'` or custom smoke reports missing `overall`. | A returned score dictionary lacks the required key. | Return finite numeric `overall` for every item. Use optional keys only for metrics and filters. |
| Batch result length mismatch. | Function dropped or added items relative to the input batch. | Return one score dictionary per input in the same order. |
| Non-finite reward values. | Division by zero, failed normalization, or unbounded penalties. | Clamp or guard computations; the smoke script rejects `NaN` and infinity. |
| Online filtering rejects all samples. | `algorithm.filter_key` points to a missing metric or the metric range is always outside thresholds. | Ensure the reward returns that key, such as `accuracy_normalized` for DAPO-style filtering, and inspect value ranges on a small batch. |
| Reward always zero for formatted answers. | Regex expects exact tags or boxed/answer format but the prompt asks for a different output format. | Align the Jinja template and reward parser; test both a positive and a negative response. |
| Android GUI reward marks explanations as correct unexpectedly. | The digit extractor uses the first occurrence of `0`, `1`, or `2`. | Keep the prompt's output-only instruction strict, or write a stricter extractor that accepts only a bare digit. |

## Backend and dependency limits

| Symptom | Meaning | Action |
| --- | --- | --- |
| CPU smoke passes but training fails at vLLM or flash-attn import. | Data/reward contracts are valid, but the full training runtime is incomplete. | Install or use a full EasyR1 CUDA runtime; route launch/debug work to `training-workflows`. |
| CUDA out-of-memory during rollout. | This is a training/runtime sizing problem, not a reward-contract problem. | Reduce rollout batch size, GPU memory utilization, prompt/media token budget, or use offload/LoRA as appropriate. |
| Android cookbook cannot run. | Device, game service, or VLM endpoint is missing. | Treat Android scripts as reference-only; first provision the external prerequisites described in [Android GUI cookbook](android-gui-cookbook.md). |
| Dataset construction tries to download model processors. | `filter_overlong_prompts` or multimodal processing needs tokenizer/processor files. | Pre-cache model/processor assets, provide approved network access, or disable filtering only for a deliberate smoke path. |

## Minimal diagnostic snippets

Check a custom reward target:

```bash
python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py \
  --target ./my_reward.py:compute_score \
  --mode auto \
  --expect-keys overall
```

Check that the default script catches a missing `overall` bug without failing the whole default run:

```bash
python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py --builtins missing-overall-guard
```

Check mixed text/image row shape statically:

```bash
python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py --builtins mixed-rows
```

If these checks pass but full training still fails, preserve the reward and dataset artifacts, collect the training error, and route to the appropriate sibling sub-skill.
