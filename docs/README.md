# AREX-Skill Documentation

This directory contains the detailed guides that support the
[AREX-Skill Library](../skills/README.md) and the [DisCo CLI](../cli/README.md).
The root [README](../README.md) gives the short project overview, benchmark
summary, and first-run path; use this index when you need operational or
development details.

## Choose a guide by task

### Getting started

| Guide | Read it when you want to… |
| --- | --- |
| [Installation Guide](installation.md) | Install DisCo, configure a model provider, install the published repository-skill collection, or build the CLI from source. |
| [AREX-Skill Library](../skills/README.md) | Understand the runtime collection layout, repository skill graphs, router behavior, and managed installation paths. |
| [DisCo CLI README](../cli/README.md) | Learn the CLI surface, packages, runtime behavior, and links to the full CLI reference. |

### Use skills for research

| Guide | Read it when you want to… |
| --- | --- |
| [DisCo Workflows](disco-workflows.md) | Run Researcher sessions, invoke repository skills, use task-specific graphs, or export selected skills to another agent. |
| [Repository Catalog](repository-catalog.md) | Browse the complete repository-skill collection by research area and package family. |
| [Imported Repo Skills Catalog](imported-repo-skills.md) | Inspect each published graph's upstream repository, source baseline, and runtime entry point. |

### Create and maintain skills

| Guide | Read it when you want to… |
| --- | --- |
| [DisCo Meta Skills](disco-meta-skills.md) | Create repository or paper skills, understand Creator meta skills, or install the portable Creator workflows into another agent. |
| [Refreshing Repo Skills](refreshing-repo-skills.md) | Refresh an existing repository skill, update provenance and routing metadata, verify the result, or prepare a maintenance PR. |
| [Architecture](architecture.md) | Understand repository layers, role boundaries, routing, deployment scopes, authoring pipelines, and transactional imports. |

### Develop DisCo or bundled workflows

| Guide | Read it when you want to… |
| --- | --- |
| [CLI documentation index](../cli/docs/index.md) | Find the complete DisCo command, provider, session, extension, SDK, security, and development references. |
| [Bundled Skills Reference](../cli/packages/coding-agent/src/disco/skills/README.md) | Modify or extend the Creator / Researcher workflow skills bundled with DisCo. |
| [Contribution Guide](../CONTRIBUTING.md) | Add or refresh skills, update generated routing and catalogs, or contribute CLI and documentation changes. |

## Recommended reading paths

### I want to try AREX-Skill

1. Follow the [Installation Guide](installation.md).
2. Read the Researcher section of [DisCo Workflows](disco-workflows.md).
3. Use the [Repository Catalog](repository-catalog.md) to find a capability.

### I want to use skills from another coding agent

1. Read the cross-agent export section of [DisCo Workflows](disco-workflows.md).
2. Follow the target-specific instructions in [DisCo Meta Skills](disco-meta-skills.md).
3. Use the [Imported Repo Skills Catalog](imported-repo-skills.md) to inspect the graph you plan to import.

### I want to create a new repository or paper skill

1. Start with [DisCo Meta Skills](disco-meta-skills.md) to identify the appropriate Creator workflow.
2. Use [DisCo Workflows](disco-workflows.md) for the construction and verification lifecycle.
3. Read [Architecture](architecture.md) if the graph, deployment scope, or routing boundary is unclear.
4. Use the [Contribution Guide](../CONTRIBUTING.md) before opening a pull request.

### I want to refresh an existing skill

1. Follow [Refreshing Repo Skills](refreshing-repo-skills.md).
2. Check the affected router and catalog entries.
3. Use the [Contribution Guide](../CONTRIBUTING.md) for the required provenance and verification information.

### I want to change the DisCo CLI

1. Start with the [CLI documentation index](../cli/docs/index.md).
2. Read [Architecture](architecture.md) for the boundary between the copied runtime, bundled skills, and managed library.
3. Read the [Bundled Skills Reference](../cli/packages/coding-agent/src/disco/skills/README.md) when changing workflow resources.
4. Follow the development and validation requirements in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Reference pages

The following pages are generated inventories or lower-level references. They
are useful when you need exact coverage or implementation detail, but are not
required for a first installation:

- [Imported Repo Skills Catalog](imported-repo-skills.md) — published graph and upstream baseline inventory.
- [Repository Catalog](repository-catalog.md) — area and family view of the 1,000 repository skill roots.
- [Architecture](architecture.md) — system boundaries and implementation model.
- [Bundled Skills Reference](../cli/packages/coding-agent/src/disco/skills/README.md) — bundled workflow contracts and artifact layouts.

This English index links to English documentation. Chinese readers should use
the documentation section in the [Chinese README](../README.zh-CN.md), which
links to the available `.zh.md` guides. The repository catalog is a generated
data page; its paths and counts should remain aligned with the runtime indexes.
