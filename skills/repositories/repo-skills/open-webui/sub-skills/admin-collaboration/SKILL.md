---
name: admin-collaboration
description: "Route auth, storage, users, groups, collaboration, and
  observability workflows in Open WebUI."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Admin and Collaboration

Use this sub-skill for operator-facing Open WebUI workflows: authentication, identity, users, groups, storage, channels, calendar, automations, analytics, telemetry, and related policy controls.

## When to use this sub-skill

Use `admin-collaboration` when the user asks about:

- auth, login, SSO, trusted headers, OAuth, LDAP, or SCIM
- users, groups, roles, or access policy
- storage backends, sessions, Redis, or database settings
- channels, calendar, automations, notifications, or analytics
- telemetry, audit, or other operator-only controls

## Read these bundled files first

- `references/workflows.md` for the operator workflow map.
- `references/troubleshooting.md` for auth, storage, Redis, and telemetry failures.
- `../../references/configuration.md` for the shared environment-variable table.
- `../deployment/references/deployment.md` if the service itself is not yet running.

## Core capabilities

- Authentication and identity bootstrap.
- User, group, and access-policy management.
- Storage, database, Redis, and session configuration.
- Collaboration features such as channels, calendar, and automations.
- Analytics, telemetry, and audit configuration.

## Typical user questions

- "How do I bootstrap the first admin user?"
- "How do I set trusted headers or SSO?"
- "How do I switch storage backends or fix Redis sessions?"
- "How do channels, calendar, or automations fit into the admin panel?"
- "How do I configure telemetry or audit logging?"

## Important boundaries

- Chat/model/provider routing belongs in `chat-models`.
- File, note, memory, and retrieval flows belong in `knowledge-files`.
- Plugins, tools, skills, pipelines, and multimodal helpers belong in `extensions`.
- Deployment and startup problems belong in `deployment` unless the issue is purely a policy or config problem.

## Success shape

A future agent should be able to:

1. Explain the policy or identity setting being changed.
2. Name the relevant backend variables or service dependencies.
3. Tell the difference between auth, storage, Redis, and telemetry failures.
4. Provide an operator-safe recovery path without guessing.
