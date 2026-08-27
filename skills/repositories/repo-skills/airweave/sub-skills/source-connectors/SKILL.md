---
name: source-connectors
description: "Implement, validate, and troubleshoot Airweave source connectors:
  decorators, registry metadata, auth/config schemas, browse trees, ACLs,
  federated search, incremental sync, and source rate limits."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Airweave Source Connectors

Use this sub-skill when a future Airweave task touches connector-facing source classes, source metadata exposed by the registry, auth/config schema behavior, connector validation, browse-tree node selection, access-control extraction, federated search sources, cursor-based incremental sync, or source-specific rate limiting.

Do not use this sub-skill for dashboard UI, Connect widget iframe/OAuth UX, MCP transport, Monke orchestration, or generic backend endpoint lifecycle work. Cross-link to sibling [backend-api](../backend-api/SKILL.md) for source-connection endpoint flows, OAuth verification, search request/response schemas, browse-tree route shapes, and API auth/org semantics.

## Route to the right reference

- Read [references/source-registry.md](references/source-registry.md) before adding a source class, changing `@source(...)` metadata, changing registry output, hiding/showing feature-flagged sources, or checking entity-definition exposure.
- Read [references/auth-and-config.md](references/auth-and-config.md) before changing auth methods, direct credential schemas, OAuth/BYOC/token-injection handling, auth-provider support, template config fields, source connection validation, or runtime token-provider creation.
- Read [references/browse-tree.md](references/browse-tree.md) before changing `supports_browse_tree`, lazy browse children, browse-node ID encoding, node-selection persistence, or targeted sync behavior.
- Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing source visibility, auth/config errors, browse-tree selection bugs, ACL over/under-grants, federated search failures, cursor regressions, source HTTP errors, concurrency issues, or rate-limit behavior.

## Connector operating rules

1. Keep connector identity in one place: the `@source(...)` decorator sets `short_name`, display name, auth methods, config classes, capability flags, labels, feature flag, cursor class, federated-search status, browse-tree support, access-control support, and source rate-limit level.
2. Preserve the BaseSource v2 contract: `create(*, auth, logger, http_client, config)`, `generate_entities(*, cursor=None, files=None, node_selections=None)`, and `validate()` are the primary connector hooks. Do not add ad-hoc credential or logger setup outside these dependencies.
3. Use the injected auth provider and `AirweaveHttpClient`. Sources should call `auth.get_token()`, `auth.force_refresh()` when supported, or direct credential models from `DirectCredentialProvider`; external HTTP calls should flow through the injected client so SSRF checks and optional source rate limits apply.
4. Put public schema fields in typed Pydantic config/auth models. Use field metadata (`is_secret`, `feature_flag`, `auth_provider_field`, `required_for_auth`, `exclude_from_ui`) deliberately because the registry turns those classes into API-visible `Fields`.
5. For continuous sync, set both `supports_continuous=True` and `cursor_class=...`; the decorator rejects continuous sources without a cursor class. Update the cursor only with stable, source-owned state and support full-sync fallback when cursor state is absent or invalid.
6. For federated sources, set `federated_search=True`, implement `search(query, limit)`, and do not pretend full sync exists. Slack intentionally raises from `generate_entities()` because it searches Slack at query time.
7. For ACL-aware sources, set `supports_access_control=True`, set `entity.access` on yielded entities, and implement `generate_access_control_memberships()` when group expansion is needed. Principal formats must stay compatible with the search broker.
8. For browse-tree sources, set `supports_browse_tree=True`, implement `get_browse_children(parent_node_id)` and `parse_browse_node_id(node_id)`, and keep emitted node IDs parsable into the metadata needed by targeted sync.
9. Keep Monke and manual credentialed workflows external. No bundled script is included for this sub-skill: the only relevant source-maintained manual artifact is the SharePoint browse-tree manual test, and it requires real Microsoft tenant credentials and external state.

## Safe validation anchors

When a backend Python 3.13 environment with Airweave and pytest is active, prefer connector-owned unit anchors first:

```bash
cd backend
python -m pytest tests/unit/platform/sources/test_http_helpers.py -q
python -m pytest tests/unit/platform/sources/test_process_entities_concurrent.py -q
python -m pytest tests/unit/platform/sources/test_sharepoint_online_acl.py -q
python -m pytest tests/unit/platform/sources/test_sharepoint_online_group_expansion.py -q
python -m pytest tests/unit/platform/sources/test_sharepoint2019v2.py -q
python -m pytest tests/unit/platform/sources/test_sharepoint2019v2_dirsync.py -q
python -m pytest tests/unit/api/test_source_feature_flags.py -q
```

Credentialed or local-stack E2E anchors are useful but not safe to run unattended: source listing/detail, federated search, source rate limits, continuous sync, entity definitions, OAuth/direct/auth-provider/token source-connection variants, and SharePoint legacy DirSync tests are cataloged in [references/troubleshooting.md](references/troubleshooting.md#validation-anchors).

The prepared backend inspection facts for this skill were CPU-only: `airweave==0.1.0` imported on Python 3.13.14, connector-relevant imports such as `airweave.schemas.source_connection`, `airweave.platform.sources._base`, and `airweave.platform.decorators` succeeded, no accelerator backend is required for this scope, and settings imports require documented environment variables with sufficiently long `STATE_SECRET` and `SVIX_JWT_SECRET` values.
