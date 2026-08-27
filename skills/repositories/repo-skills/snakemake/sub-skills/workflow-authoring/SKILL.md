---
name: workflow-authoring
description: "Write, refactor, and troubleshoot Snakemake 9.23.1 Snakefiles,
  rules, wildcards, modules, checkpoints, includes, and
  script/notebook/wrapper/CWL hooks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Workflow Authoring

Use this sub-skill when the task is about Snakefile language semantics or DAG construction: rules, wildcards, directives, helper functions, `expand()`, `glob_wildcards()`, `multiext()`, output flags, includes, modules, checkpoints, scripts, notebooks, wrappers, CWL hooks, and authoring-time validation.

## Route by Task

- **Rule syntax or helper APIs**: read `references/language-reference.md` for Snakemake 9.23.1 rule anatomy, wildcard behavior, input functions, shell formatting, output flags, and hook directives.
- **Refactoring workflow structure**: read `references/workflow-patterns.md` for safe patterns around named IO, reusable rule files, modules, checkpoints, ambiguity reduction, and script extraction.
- **Authoring errors**: read `references/troubleshooting.md` for parser/syntax errors, wildcard ambiguity, `MissingInputException`, `InputFunctionException`, checkpoint misuse, module surprises, optional script/notebook dependencies, and stale `--reason` commands.
- **Starter example**: run `python scripts/minimal_snakefile.py --help` or generate a tiny isolated workflow with `python scripts/minimal_snakefile.py --output-dir demo-workflow`.

## Boundaries

- Use `../configuration-data/SKILL.md` for config files, schemas, tabular metadata, PEP/sample sheets, and validation policy beyond simple Snakefile reads.
- Use `../execution-cli/SKILL.md` for CLI flags, profiles, targets, scheduling, resources at execution time, and dry-run strategy beyond authoring smoke checks.
- Use `../deployment-storage/SKILL.md` for conda, containers, wrappers with environment setup, storage plugins, and remote provider credentials.
- Use `../debugging-reporting/SKILL.md` for lint/report/test artifacts, CI, generated reports, benchmark outputs, and deep runtime debugging.
- Use `../python-api-plugins/SKILL.md` for programmatic execution through Snakemake Python APIs or plugin development.

## Default Authoring Validation

From the workflow directory, prefer a current Snakemake 9.23.1 loop:

```bash
snakemake --snakefile Snakefile --cores 1 --dry-run --printshellcmds
snakemake --snakefile Snakefile --cores 1 --dry-run --dag > dag.dot
python -m snakemake --help
```

Do not copy older commands that use `--reason`; Snakemake 9.23.1 does not accept that flag, although dry-run output still reports job reasons.
