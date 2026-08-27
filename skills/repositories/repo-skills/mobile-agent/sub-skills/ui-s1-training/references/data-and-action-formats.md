# UI-S1 Data and Action Formats

UI-S1 GUI trajectory data is JSONL. Each row should describe a goal and a sequence of steps with screenshots and actions.

## Minimum row shape

```json
{
  "goal": "Open Settings and enable dark mode",
  "steps": [
    {
      "screenshot": "images/000.png",
      "action_content": {"action": "click", "coordinate": [500, 300]},
      "check_options": {"action": "click", "coordinate": [500, 300], "candidate_bbox": []}
    }
  ]
}
```

`eval_qwenvl.py` normalizes `check_options` from `action_content` when missing and may add `candidate_bbox` from `bbox`, but training/evaluation data is easier to debug if `check_options` is present up front.

Validate:

```bash
python sub-skills/ui-s1-training/scripts/validate_ui_s1_jsonl.py --jsonl train.jsonl
python sub-skills/ui-s1-training/scripts/validate_ui_s1_jsonl.py --jsonl eval.jsonl --require-check-options
```

## Response/action tags

The `JsonFormat` formatter uses tagged responses:

```text
<think>
...
</think>
<action>
{"action": "click", "coordinate": [500, 300]}
</action>
```

When thought is disabled, `<action>...</action>` remains the important machine-readable part. The action content must parse as JSON.

## Common repairs

- Add missing `goal` text.
- Ensure `steps` is a non-empty list.
- Add `screenshot` for every step.
- Add object-valued `action_content` for every step.
- Add or normalize `check_options` before SOP/eval data if the evaluator should compare candidate boxes or exact actions.
