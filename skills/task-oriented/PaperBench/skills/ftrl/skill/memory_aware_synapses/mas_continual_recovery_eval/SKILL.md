---
name: mas_continual_recovery_eval
description: Evaluate MAS in a bounded sequential-learning recovery and report forgetting plus mechanism checks.
---
# MAS Continual Recovery Evaluation
Use for reduced MAS recovery when full datasets are unavailable. Compare task-1 score before and after finetuning/MAS, and accept only if MAS reduces forgetting with mechanism checks. Validate with `python tests/test_eval.py`.
