# CLI and loader troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `invalid choice` from argparse | Command name typo | Re-run with `swarms --help` or `swarms tips`. |
| `--markdown-path` missing | `load-markdown` needs a file or directory | Pass a concrete path to a markdown file or folder. |
| YAML validation fails | Missing `agents` list or malformed agent block | Validate the YAML shape before running the command. |
| Markdown loader rejects a file | No YAML frontmatter or malformed frontmatter | Add a top `---` block with `name` and `description`. |
| `max_loops` cannot be parsed | Non-numeric text other than `auto` | Use an integer or the literal string `auto` for the agent command family. |
| `autoswarm` refuses to start | Task or model missing | Provide both `--task` and `--model`. |
| CLI command appears to run but no model result appears | Live provider call failed after the CLI layer succeeded | Check the provider key, model name, and network access. |

## Recovery order

1. Confirm the command name and the required flags.
2. Validate the YAML or markdown file without running a live swarm.
3. Check provider keys only after the parser and loader shapes are correct.
4. Use `setup-check` when you need an environment diagnosis before anything else.
