# Language instructions and deterministic expansion

RoboTwin separates task execution from language conditioning. The task class returns episode-specific placeholder values, while `description/task_instruction/<task_name>.json` holds template sentences for the `seen` and `unseen` language splits.

## Task instruction JSON shape

A task instruction file has this shape:

```json
{
  "full_description": "detailed task flow in plain language",
  "schema": "{A} names the first object, {a} names the arm used for {A}",
  "preference": "style or length constraints for generated/manual instructions",
  "seen": ["Grab {A} with {a} and place it on {B}."],
  "unseen": ["Put {A} on {B} using {a}."]
}
```

Required behavior:

- `full_description`, `schema`, and `preference` are prompt inputs for credential-bound generators, but they are also useful human documentation when instructions are hand-authored.
- `seen` and `unseen` are arrays of template strings. Hand-written entries are valid; hosted LLM generation is optional.
- Uppercase placeholders such as `{A}`, `{B}`, `{C}` normally represent objects or target objects.
- Lowercase single-letter placeholders such as `{a}`, `{b}` normally represent arms. The expander formats values like `left` and `right` as `the left arm` and `the right arm`.
- Templates should contain all non-arm placeholders needed for the task. Arm placeholders may be omitted in some templates to increase language variety, as long as all non-arm placeholders still match the episode info.

## Episode info from `play_once()`

During data collection or evaluation, `play_once()` returns an info dictionary. The language expander uses the nested `info` mapping:

```python
self.info["info"] = {
    "{A}": "001_bottle/base0",
    "{B}": "003_plate/base0",
    "{a}": str(arm_tag),
}
return self.info
```

Placeholder values can be:

- **Asset description IDs** such as `001_bottle/base0`. The expander resolves these to `description/objects_description/001_bottle/base0.json` and picks a phrase from that JSON.
- **Plain phrases** such as `red block` or `green block`. The expander inserts them directly.
- **Arm names** such as `left` or `right` for lowercase single-letter placeholders. The expander wraps them as natural arm phrases.

If a value contains `/` or `\\`, it is treated like an object-description ID. Make sure the matching object-description JSON exists, or use a plain phrase instead.

## Object-description JSON shape

Object descriptions are simple and can be hand-authored:

```json
{
  "raw_description": "bottle",
  "seen": ["red bottle", "plastic bottle", "bottle with red cap"],
  "unseen": ["shiny red bottle", "bottle with white label"]
}
```

For `seen` expansion, phrases come from the object's `seen` array. For `unseen` expansion, phrases come from `unseen` when available and fall back to `seen` otherwise. Keep descriptions short, concrete, and manipulation-relevant.

## Template filtering rules

For each episode, a template is usable when either:

1. its placeholders exactly match the episode info keys after removing braces, or
2. the only placeholders it omits are arm placeholders such as `{a}` or `{b}`.

Examples for episode info keys `{A}`, `{B}`, `{a}`:

| Template | Accepted? | Reason |
| --- | --- | --- |
| `Place {A} left of {B} using {a}.` | yes | Exact placeholder match. |
| `Place {A} left of {B}.` | yes | Omits only the arm placeholder. |
| `Place {A}.` | no | Omits non-arm placeholder `{B}`. |
| `Place {A} left of {B} using {c}.` | no | Uses unknown placeholder `{c}`. |

When expansion reports no valid instructions, compare the template placeholders against `play_once()`'s returned `self.info["info"]` keys first.

## Seen and unseen splits

- `seen` instructions are usually training/default language variants.
- `unseen` instructions are held-out language variants used to stress language generalization.
- Task configs use `language_num` to cap how many variants are generated per episode.
- Task configs use `eval_instruction: seen` or `eval_instruction: unseen` to choose the evaluation split.
- Collection code embeds generated `seen` instructions into the trajectory by default; evaluation utilities may request either split.

Avoid leaking validation content: if the user is intentionally evaluating language generalization, do not copy all unseen phrases into the seen split just to make a model succeed.

## Bundled deterministic expander

The repository's deterministic part is placeholder expansion, not task/object/template generation. Use this sub-skill's bundled script when the user wants local expansion without credentials:

```bash
python <this-sub-skill>/scripts/generate_episode_instructions.py \
  --repo-root . \
  --task beat_block_hammer \
  --setting demo_clean \
  --max-num 5 \
  --dry-run
```

Useful options:

- `--scene-info PATH`: read a specific `scene_info.json` instead of discovering it from the task config.
- `--task-json PATH`: read a standalone task-instruction JSON fixture.
- `--object-description-root PATH`: use a custom object-description root.
- `--output-dir PATH`: write to a specific output directory. Defaults to an `instruction/` directory beside `scene_info.json`.
- `--filename-style xpolicylab|legacy`: choose `episode_0000000.json` or `episode0.json` output names.
- `--seed N`: deterministic seed used for template order and object phrase selection.
- `--dedupe`: remove duplicate expanded strings while preserving order.
- `--dry-run`: print a preview and perform no writes.

The script supports both the current collection layout (`data/<task_config>/<task_name>/<embodiment>/scene_info.json`) and the legacy description utility layout (`data/<task_name>/<setting>/scene_info.json`) when discovering scene info from `--setting`.

## Manual authoring style

For robust instructions:

- Use short action verbs: grab, lift, place, press, open, close, stack, rotate, scan, hand over.
- Include all task-critical relations: left/right of, inside, on top of, into, away from, open enough, press down, strike, shake horizontally.
- Avoid exact coordinates in language unless the task is explicitly coordinate-based.
- Avoid hard-coding object colors if the placeholder may resolve to different object variants.
- Keep templates grammatical after replacing both object phrases and arm phrases.
- Include some arm-free variants when arm choice is implicit, but not when the language condition must force a specific arm.

## Interaction with data collection

Task authoring stops when task code, configs, and language templates are coherent. When the user asks to collect demonstrations, validate HDF5 trajectories, inspect downloaded datasets, or convert to LeRobot/XPolicyLab formats, route to `data-pipeline` after confirming the task authoring inputs are ready.
