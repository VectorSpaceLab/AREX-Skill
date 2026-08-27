---
name: workflows-and-tools
description: "Author, validate, test, and troubleshoot Galaxy tool wrappers,
  tool tests, workflow Format2 YAML, CWL conversion surfaces, tool dependency
  hints, and tool-util CLIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Galaxy Workflows and Tools

Use this sub-skill when a task involves Galaxy tool XML or YAML wrappers, tool tests, workflow framework tests, Format2 workflow YAML, CWL conversion surfaces, tool panel loading, dependency requirements, mulled helpers, or `galaxy-tool-util` command-line utilities.

## Start Here

- For tool wrappers and tests, read [Tool Development](references/tool-development.md).
- For Format2 workflow YAML, workflow framework tests, inline user-defined tools, and CWL boundaries, read [Workflow Development](references/workflow-development.md).
- For safe CLI checks and installed `galaxy-tool-util` entry points, read [CLI Reference](references/cli-reference.md) and use [scripts/inspect_tool_util.py](scripts/inspect_tool_util.py).
- For parser, validation, dependency, workflow conversion, and tool panel failures, read [Troubleshooting](references/troubleshooting.md).

## Boundaries

- Stay here for tool XML structure, `<tests>` blocks, YAML test files, `galaxy-tool-test`, `galaxy-tool-format`, `galaxy-tool-upgrade-advisor`, `validate-test-format`, workflow framework tests, Format2 YAML, CWL conversion surfaces, tool panel behavior, and mulled/dependency command hints.
- Route datatype definitions, persistent tool data tables, `.loc` files, and deep data-manager table behavior to [Data and Storage](../data-and-storage/SKILL.md). Data managers appear here only as special Galaxy tools with admin-only behavior and tool-test implications.
- Route API import/invocation of already-authored workflows to [API Automation](../api-automation/SKILL.md).
- Route Tool Shed publishing, repository metadata, installation, and distribution operations to [Tool Shed Operations](../tool-shed-operations/SKILL.md).

## Safe Default Workflow

1. Identify whether the artifact is a tool wrapper, tool test file, workflow definition, workflow test file, CWL conversion case, dependency/mulled check, or tool panel configuration issue.
2. Run local, non-network static checks first: XML parse/format diff, test-format schema validation, import/help checks for `galaxy-tool-util`, and upgrade advice.
3. Use server-backed commands such as `galaxy-tool-test` only when the user supplies a Galaxy URL and API key or explicitly asks to use a running local Galaxy.
4. Treat conda, container registry, BioContainers, and mulled build/list/search operations as external dependency management: explain network/runtime requirements before running them.

## Quick Commands

```bash
python scripts/inspect_tool_util.py --check-imports --help-checks
python scripts/inspect_tool_util.py --tool-xml path/to/tool.xml --test-file path/to/tests.yml
python -m galaxy.tool_util.format --diff path/to/tool.xml
python -m galaxy.tool_util.validate_test_format path/to/tests.yml
python -m galaxy.tool_util.upgrade.script path/to/tool.xml --profile-version 24.2
```

Use `galaxy-tool-test` only with a running Galaxy target, for example: `galaxy-tool-test --galaxy-url http://localhost:8080 --key "$GALAXY_API_KEY" --tool-id TOOL_ID --test-index 0`.
