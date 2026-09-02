---
name: cot_equation_calculator
description: Safely check and repair simple arithmetic equations inside chain-of-thought reasoning traces.
---

# Chain-of-Thought Equation Calculator

Use this skill when an arithmetic chain-of-thought trace contains explicit equations and you need to verify or repair calculation-only errors. Do not use it to validate semantic reasoning, create prompts, or score final answers directly.

## Inputs

- Reasoning text containing equation-like spans such as `2 * 3 = 6`.
- Optional repair flag.
- Optional operator and expression-length bounds.

## Outputs

- Equation check records with expression, stated result, computed result, and correctness.
- Aggregate correctness flag.
- Optional repaired text that changes only incorrect stated numeric results.

## Workflow

1. Find simple equation spans in the reasoning trace.
2. Parse arithmetic expressions with Python `ast`.
3. Allow only numeric constants and arithmetic operators.
4. Compare computed and stated results.
5. If repair is requested, replace only the stated numeric result for safe equations.

## Validation

Run:

```bash
python scripts/cot_equation_calculator.py --self-test
python -m unittest discover -s tests
```

The tests cover correct equations, incorrect equations, repaired traces, multiple equations, and unsafe expressions that must be ignored.

## Limitations

The calculator intentionally refuses variables, function calls, and arbitrary Python syntax. It cannot decide whether the chosen equation is semantically appropriate for the word problem.
