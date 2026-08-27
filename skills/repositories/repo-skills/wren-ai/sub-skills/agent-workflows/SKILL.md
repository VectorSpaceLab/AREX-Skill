---
name: agent-workflows
description: "Guide Wren CLI-served agent workflow guides, discovery-stub
  installation, wren skills retrieval, guided prompt shaping, dlt SaaS
  ingestion, and Wren skill authoring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Wren Agent Workflows

Use this sub-skill when an agent needs Wren's own workflow guides, the `wren
skills` command, the discovery stub, `wren ask`, dlt/SaaS ingestion, or authoring
new guide content that ships with the CLI.

## Discover and Retrieve Guides

Install the CLI first, then inspect the version-matched guide inventory:

```bash
pip install wrenai
wren skills list
wren skills get onboarding
wren skills get usage --full
wren skills get dlt-connector --script introspect_dlt
```

The current guide names are `onboarding`, `usage`, `generate-mdl`,
`dlt-connector`, `enrich-context`, and `genbi`. Use `--full` for bundled
references and `--script` to print a named bundled helper.

## Route by Intent

| Intent | Guide |
| --- | --- |
| First install, connection, project, and first query | `onboarding` |
| Day-to-day governed data question | `usage` |
| Build MDL from a database schema | `generate-mdl` |
| Load SaaS data through dlt and create a Wren project | `dlt-connector` |
| Add business rules, definitions, or named metrics | `enrich-context` |
| Build or deploy a dashboard application | `genbi` |

Read the returned guide before carrying out its multi-step workflow. These
guides are package data, so their contents match the installed CLI version.

## Prompt Shaping

`wren ask` produces a prompt; it does not query a database:

```bash
wren ask "How many active customers did we have last month?" --guided
wren ask "How many active customers did we have last month?" --direct
```

Choose exactly one mode. `--guided` supplies a stricter workflow for a weaker
agent; `--direct` is a minimal wrapper for a stronger agent.

## dlt Path

For SaaS data, use the dlt guide before assuming a direct Wren connector exists.
The normal flow is source API -> dlt -> local DuckDB -> generated Wren project
-> validate/build/query. Use the bundled helper only with a local DuckDB file
and review generated models before a live query.

## Authoring Rule

New Wren workflow guides ship as package data, not as discovery-stub directories.
Use the CLI skill-content location in the package source when maintaining the
repository, add a matching guide name, and test `wren skills get` delivery.

## References and Helper

- Read `references/agent-skills.md` for install and delivery behavior.
- Read `references/wren-ask.md` for explicit prompt-mode rules.
- Read `references/dlt-workflow.md` before creating a project from SaaS/DuckDB
  data.
- Read `references/skill-authoring.md` when changing a CLI-served guide.
- Read `references/troubleshooting.md` for stub, retrieval, dlt, and credential
  failures.
- Run `scripts/introspect_dlt_project.py --help` before using its local
  DuckDB-to-project generator.

## Guardrails

- Never ask a user to paste database or SaaS credentials into chat. Use an
  environment-backed secret file or provider-supported secret mechanism.
- Do not install a discovery stub as a substitute for installing `wrenai`; the
  stub only teaches a compatible agent how to discover the CLI.
- Do not place a new guide only in a repository-root skill directory when it is
  meant to ship with the `wren` command.
