---
name: data-and-storage
description: "Manage Galaxy datatypes, metadata, dataset storage, object stores,
  file sources, data managers, tool data tables, and storage safety boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Galaxy Data and Storage

Use this sub-skill when a task involves Galaxy datatypes, sniffers, datatype metadata, dataset storage, object stores, file sources, data managers, tool data tables, `.loc` entries, or storage cleanup risk assessment.

## Start Here

- For datatype implementation, registration, metadata, composite formats, and sniffer safety, read [Data Formats](references/data-formats.md).
- For data manager XML/JSON contracts and tool-data table entries, read [Data Managers](references/data-managers.md).
- For object-store, file-source, user template, credential, and storage-test planning, read [Object Stores and Files](references/objectstores-and-files.md).
- For common failures and conservative triage, read [Troubleshooting](references/troubleshooting.md).
- For a quick bounded-sniffer review, run `python scripts/check_datatype_sniffer.py PATH_OR_STDIN`.

## Routing Boundaries

- Stay here for datatype classes, `datatypes_conf.xml` registration, `sniff`, `set_meta`, `set_peek`, data-manager outputs, tool-data tables, object-store configuration concepts, file-source credentials, dataset cleanup safety, and data/storage tests.
- Route broad Galaxy config placement, startup, `galaxy.yml` editing, and admin deployment planning to [Configuration and Admin](../configuration-and-admin/SKILL.md).
- Route tool XML mechanics, wrapper tests, workflow YAML, and dependency declarations to [Workflows and Tools](../workflows-and-tools/SKILL.md).
- Route upload/download API calls, history dataset automation, and API-client scripting to [API Automation](../api-automation/SKILL.md).

## Safety Defaults

- Never run cleanup, purge, migration, cloud object-store, or credentialed file-source actions without explicit user approval, target confirmation, backup/rollback context, and dry-run or read-only checks first.
- Treat sniffers as production hot paths: they must inspect bounded prefixes or bounded header/sample helpers, never entire files.
- Treat user file sources and object-store templates as secret-bearing configuration; do not print, persist, or invent credentials.
- Prefer local/unit tests and template/model validation before remote integration tests; skip cloud or network tests unless credentials and disposable resources are explicitly supplied.
