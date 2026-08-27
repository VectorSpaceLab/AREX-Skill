# Task Memory and Evolution

## Individual mode

Use individual mode for one task or for debugging a task list without cross-task memory effects. It does not share persistent tips/shortcuts across tasks.

Command builder shape:

```bash
python sub-skills/mobile-agent-e/scripts/build_mobile_agent_e_command.py \
  --instruction "Open Notes and write a reminder" \
  --setting individual \
  --log-root private-logs/mobile-agent-e \
  --run-name notes-debug
```

## Evolution mode

Use evolution mode when tasks should update and reuse shared tips/shortcuts across a sequence:

```bash
python sub-skills/mobile-agent-e/scripts/build_mobile_agent_e_command.py \
  --tasks-json tasks.json \
  --setting evolution \
  --specified-tips-path seed_tips.txt \
  --specified-shortcuts-path seed_shortcuts.json \
  --log-root private-logs/mobile-agent-e \
  --run-name app-suite
```

Evolution writes persistent memory under the run directory. Inspect those files after a failure before blindly increasing iteration limits.

## Repeated-action control

Relevant knobs:

- `--max_itr`: maximum steps per task.
- `--max_consecutive_failures`: stop after repeated failures.
- `--max_repetitive_actions`: stop after repeated identical actions.
- `--temperature`: model sampling; keep low for reproducibility.
- `--enable_experience_retriever`: optional retrieval from prior experience.
- `--screenrecord`: live run recording; increases side effects/storage.

For repeated-action debugging, reduce to one task in individual mode, inspect screenshots/logs, then seed corrected tips before retrying evolution mode.
