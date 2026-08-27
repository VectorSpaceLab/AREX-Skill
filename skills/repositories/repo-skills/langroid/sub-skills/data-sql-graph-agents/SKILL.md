---
name: data-sql-graph-agents
description: "Use Langroid structured-data agents for table/CSV/Pandas, SQL,
  Neo4j, ArangoDB, and CSV-to-knowledge-graph workflows with schema/context
  setup and safe query validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data, SQL, and Graph Agents

Use this sub-skill for structured data questions, tabular analysis, SQL-backed
Q&A, and graph construction or graph Q&A.

## Choose the right agent

- Table, CSV, or Pandas analysis -> TableChatAgent
- SQL database Q&A -> SQLChatAgent
- Neo4j graph Q&A or writes -> Neo4jChatAgent
- ArangoDB graph Q&A or writes -> ArangoChatAgent
- CSV-to-knowledge-graph bootstrapping -> CSVGraphAgent

## Route elsewhere

- Unstructured document RAG -> sibling skill `retrieval-doc-chat`
- Provider, model, or API-key setup -> sibling skill `llm-provider-config`
- Generic Task / Tool orchestration -> sibling skill `agents-tasks-tools`

## Start here

- [API reference](references/api-reference.md)
- [Workflow patterns](references/data-agent-workflows.md)
- [Database and schema config](references/database-and-schema-config.md)
- [Security and validation](references/security-and-validation.md)
- [Troubleshooting](references/troubleshooting.md)
- [Safety smoke script](scripts/data_agent_safety_smoke.py)

## Operating rules

- Prefer the least-privilege, validation-first path.
- Keep `TableChatAgentConfig.full_eval=False` unless the input is fully trusted.
- Keep `SQLChatAgentConfig.allow_dangerous_operations=False` and extend
  `allowed_statement_types` only when writes are intended.
- Keep Neo4j and Arango dangerous operations disabled by default.
- Use schema or context helpers before asking the model to write SQL or graph
  queries.
- Use the bundled smoke script to inspect defaults or validate a SQL, Cypher,
  or AQL string locally without touching a live service.
- If the question is really about model/provider configuration, hand it off to
  the provider-config skill instead of forcing it through this one.
