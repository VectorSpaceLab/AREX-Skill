# Mobile-Agent-E Data Formats

## Task list JSON

Recommended object-root format:

```json
{
  "length": 2,
  "scenario": "testing",
  "scenario_id": 0,
  "tasks": [
    {
      "task_id": "testing_0",
      "instruction": "Open Notes, create a new note, and write a joke in it.",
      "type": "single_app",
      "apps": ["Notes"]
    },
    {
      "task_id": "testing_1",
      "instruction": "Check today's weather on Google and create a new note about it.",
      "type": "multi_app",
      "apps": ["Google", "Notes"]
    }
  ]
}
```

The runtime also accepts a bare list in code, but object-root files preserve scenario metadata and allow length checks.

Validate with:

```bash
python sub-skills/mobile-agent-e/scripts/validate_mobile_agent_e_tasks.py --tasks-json tasks.json
```

## Tips and shortcuts

- `--specified_tips_path`: seed textual tips.
- `--specified_shortcuts_path`: seed JSON shortcuts.
- In evolution mode, the seed files are copied into persistent files under `log_root/run_name` and then updated across tasks.
- In individual mode, persistent cross-task files are not shared.

Keep tips/shortcuts private if they include app names, user data, accounts, or credentials.
