# Data Preparation Workflow

## 1. Identify the schema

- `conversations` -> SFT or GRPO
- `prompt` + `chosen` + `rejected` -> DPO
- `label` -> classification

## 2. Check the media layout

- Images and videos may be strings or lists.
- Relative paths should resolve through the declared media folder.
- Use URLs only when the downstream workflow can reach them.

## 3. Apply the reasoning rules

- `Qwen3-VL-*-Thinking` requires a non-empty `reasoning` field on each assistant turn when reasoning is enabled.
- `Qwen3.5` can mix reasoning and non-reasoning samples.
- DPO must keep `chosen_reasoning` and `rejected_reasoning` in sync.

## 4. Run the validator

Use the bundled helper before the training or serving route:

```bash
python scripts/validate_dataset.py dataset.json --mode auto --check-media-paths --image-folder /data/images
```

## 5. Decide if the sample belongs here

- If the issue is the JSON shape, stay in this sub-skill.
- If the JSON is valid but the user wants a training command, hand off to the appropriate training sub-skill.

## Notes for common media cases

- For multi-image samples, the model consumes a list of image paths.
- For video samples, prefer one clear clip path per turn when possible.
- Keep `fps` and `nframes` exclusive.
