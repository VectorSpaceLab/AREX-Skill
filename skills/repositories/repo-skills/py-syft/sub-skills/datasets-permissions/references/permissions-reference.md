# Permissions reference

`syft.pub.yaml` controls access for files under a datasite directory. The nearest permission file on the path wins; parent and child files do not merge. `terminal: true` prevents deeper overrides.

Rule example:

```yaml
terminal: false
rules:
  - pattern: "**/*.csv"
    access:
      read: ["alice@example.com"]
      write: []
      admin: []
```

Patterns support exact paths, globs, and template variables such as `{{.UserEmail}}`. More specific patterns beat broad `**` patterns.

High-level `syft_perms` API:

```python
import syft_perms as sp
file = sp.open("data.csv")
file.grant_read_access("bob@example.com")
file.has_read_access("bob@example.com")
file.explain_permissions("bob@example.com")
```
