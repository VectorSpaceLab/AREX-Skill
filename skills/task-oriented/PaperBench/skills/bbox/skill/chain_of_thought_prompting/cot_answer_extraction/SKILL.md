---
name: cot_answer_extraction
description: Extract and normalize final answers from chain-of-thought outputs without scoring intermediate reasoning text.
---

# Chain-of-Thought Answer Extraction

Use this skill when a model or recovery harness emits reasoning followed by a final answer and you need the shortest canonical answer span for scoring. Do not use it to build prompts, judge rationale quality, or run an external calculator.

## Inputs

- Raw output text.
- Task type: `numeric`, `multiple_choice`, `yes_no`, `date`, `symbolic`, or `plan`.
- Optional final-answer markers and numeric tolerance settings.

## Outputs

- Raw text.
- Extracted final answer.
- Normalized answer.
- Diagnostics with marker and fallback information.

## Workflow

1. Search from the end of the output for markers such as `The answer is`, `So the answer is`, or `Answer:`.
2. Extract the following short span and ignore earlier intermediate numbers.
3. If no marker appears, fall back to a task-specific extraction from the end of the text.
4. Normalize according to task type.
5. Preserve diagnostics so recovery can distinguish explicit marker extraction from fallback behavior.

## Validation

Run:

```bash
python scripts/cot_answer_extraction.py --self-test
python -m unittest discover -s tests
```

Tests cover numeric traces, multiple-choice letters, yes/no outputs, dates, and symbolic answers.

## Limitations

The extractor intentionally keeps normalization conservative. It does not infer answers from unsupported world knowledge and it does not decide whether the reasoning path is faithful.
