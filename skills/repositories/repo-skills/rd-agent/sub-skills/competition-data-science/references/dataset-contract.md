# Data-science dataset contract

## Required task description

Include the task objective, target, row/entity semantics, available columns, train/test or temporal split, metric direction, missing-value rules, prohibited leakage, and exact submission format. Put this in a stable `description.md` that the agent can read without credentials.

## Preparation contract

`prepare.py` should create or identify training data, test data, a submission template, and (when the task supports it) a standard answer or local evaluation input. Make it deterministic and idempotent where possible. Record source checksums or dataset version outside the reusable skill.

## Validation contract

`valid.py` should reject missing columns, duplicate identifiers, wrong row counts, invalid dtypes, and malformed output. `grade.py` should define the metric and never silently score a different file. Keep validation separate from grading so a malformed submission cannot look like a low model score.

## Debugging

A debug sampler may reduce rows/features but must preserve schema and label semantics. For grouped or temporal data, sample complete groups or contiguous windows. Always print the resulting shape, columns, target distribution, and split boundaries before the agent loop.
