---
name: gedi_multiclass_control
description: Build GeDi true/false control-code inputs for multi-class and zero-shot topic control with exactly two class-conditional passes.
---

# GeDi Multi-class Control

## When to use
Use this skill when adapting GeDi to many labels or topic control without one forward pass per class. It is appropriate for AG-News-like labels and zero-shot topic words.

## Inputs
- A label or topic string.
- Text or prompt.
- Positive control token, default `true`.
- Negative control token, default `false`.

## Outputs
- Positive/control sequence.
- Negative/anti-control sequence.
- Metadata including label, token count hint, and `control_passes=2`.

## Workflow
1. Normalize the label without changing its semantic content.
2. Build `true <label> <text>` and `false <label> <text>`.
3. During training, use true pairs for matching class/text and false pairs for nonmatching class/text.
4. During generation, use true as desired control and false as anti-control.
5. Record whether the label is seen or zero-shot when that information is supplied.

## Validation
Run:

```bash
python tests/test_multiclass.py
```

## Limitations
This skill formats the control-code pairs; it does not tokenize with a model or evaluate topic relevance.
