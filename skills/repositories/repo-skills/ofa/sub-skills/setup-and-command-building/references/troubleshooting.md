# Troubleshooting

## Common problems

### `train.py` or `evaluate.py` cannot import OFA modules

- Confirm the repo root and bundled `fairseq/` fork are visible to Python.
- Run `scripts/check_ofa_environment.py --check-clis`.
- If Fairseq resolves from a different installed package, fix the import path before doing anything else.

### CLI help works, but actual runs crash immediately

- Usually means the environment is missing a GPU backend, checkpoint, dataset, or task-specific override.
- Check the task sub-skill for the data layout and required files.
- Use the root environment checker with `--require-cuda` if the workflow is supposed to be GPU-backed.

### A copied shell script fails because of port or GPU collisions

- Give each concurrent job a unique `MASTER_PORT`.
- Make sure the visible GPU list matches the job's world size.
- Prefer `scripts/render_ofa_command.py` when you need to rewrite the launch shape safely.

### `--model-overrides` JSON is malformed

- Re-render the command with the helper instead of hand-editing nested JSON.
- Keep the override values minimal: data path, BPE directory, selected columns, and task-specific files.

## Recovery order

1. Environment check.
2. Input validator in the owning sub-skill.
3. Command render.
4. Heavy job only after the first three steps pass.
