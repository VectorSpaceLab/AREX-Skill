# Repo-Level Registry and Daemon Summary

For detailed instructions, use `sub-skills/integrations-and-extensions/references/registry-and-daemon.md`.

Use the registry when users need CRG across multiple repositories:

```bash
code-review-graph register /path/to/repo --alias repo
code-review-graph repos
```

Use the daemon only when several repositories should stay updated automatically:

```bash
code-review-graph daemon add /path/to/repo --alias repo
code-review-graph daemon start
code-review-graph daemon status
```

Invalid paths, duplicate aliases, stale PID files, and moved repositories should be handled explicitly rather than silently ignored.