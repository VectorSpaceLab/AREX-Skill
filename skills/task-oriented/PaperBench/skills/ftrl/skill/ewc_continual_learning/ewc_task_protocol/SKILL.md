---
name: ewc_task_protocol
description: Build deterministic sequential-task protocols for Elastic Weight Consolidation recovery experiments where old-task data is withheld after task switches.
---

# EWC Task Protocol

Use this skill when a continual-learning recovery needs auditable task ordering and no-rehearsal boundaries. Do not use it to mix old-task examples into new-task training unless the experiment explicitly studies rehearsal rather than core EWC.

## Inputs

- Task arrays or a deterministic seed for the bundled reduced fixture.
- Task order and active training task.
- Optional source provenance for real datasets or synthetic proxies.

## Outputs

- Protocol JSON with tasks, labels, task order, active train task, evaluation tasks, and source metadata.
- A data item log suitable for `recovery/logs/generated_data_item.json`.

## Workflow

1. Create or load task datasets.
2. Record the task switch order.
3. Expose only the active task for training.
4. Keep evaluation tasks separate for retention checks.
5. Validate that task-B training excludes task-A examples.

## Validation

Run:

```bash
python tests/test_task_protocol.py
```

## Limitations

The bundled fixture is a reduced synthetic proxy, not full permuted MNIST. It is valid only when soft-mode reduced recovery is declared and mechanism checks are recorded.
