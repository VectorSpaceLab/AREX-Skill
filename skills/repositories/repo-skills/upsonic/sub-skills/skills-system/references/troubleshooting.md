# skills-system Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A skill directory fails validation | The frontmatter is missing required fields or the directory name does not match the skill name. | Fix the YAML first, then rerun the directory validator. |
| Duplicate skill names appear after load | A later loader intentionally overwrote an earlier loader. | Reorder the loaders or rename the conflicting skill. |
| Dependency warnings keep appearing | A dependency is missing or the graph contains a cycle. | Add the missing dependency or break the cycle before using strict mode. |
| A script or reference cannot be read | The path is wrong or the file is not included in the skill tree. | Bundle the file inside the skill tree and re-run validation. |

## Smoke check

```bash
python sub-skills/skills-system/scripts/validate_skill_dir.py --allow-disco-fields sub-skills/skills-system
```
