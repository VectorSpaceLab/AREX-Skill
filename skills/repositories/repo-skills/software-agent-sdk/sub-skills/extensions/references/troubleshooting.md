# Extensions Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A skill is missing | Bad name, bad directory shape, or loaded from the wrong path. | Ensure the skill directory contains `SKILL.md` and the frontmatter `name` matches the directory basename. |
| Project skills are loaded but hidden content appears in the prompt | The skill is marked to disable model invocation or is triggered unexpectedly. | Check `disable_model_invocation`, triggers, and `AgentContext.disabled_skills`. |
| A hook blocks with exit code 2 | That exit code is intentional policy blocking. | Review the hook command output and decide whether to fix the workspace state or relax the policy. |
| `.mcp.json` is ignored | Legacy and AgentSkills loading rules differ. | Use `.mcp.json` only with `SKILL.md` AgentSkills; legacy `.md` skills use frontmatter MCP declarations. |
| Secrets disappear during validation | They were redacted or empty. | Ensure the input is not the redaction sentinel and that any required cipher context is available. |
