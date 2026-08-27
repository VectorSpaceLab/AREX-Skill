---
name: datasets-permissions
description: "Operate PySyft dataset publication, mock/private resolution, syft
  URLs, and SyftBox permission APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# datasets-permissions

Use this sub-skill for `create_dataset`, mock/private dataset separation, `resolve_dataset_file_path`, `load_dataset_code`, `syft://` paths, dataset visibility/deletion, `upload_private`, `syft.pub.yaml`, `syft_permissions`, and `syft_perms` ACL questions.

## Workflow

1. Confirm DO and DS are accepted peers and synced; otherwise route to [../auth-sync-transport/SKILL.md](../auth-sync-transport/SKILL.md).
2. DO creates a dataset with public mock files and private owner-side files.
3. DS lists/reads mock files after sync and tests analysis locally.
4. Inside a submitted job, `resolve_dataset_file_path(...)` resolves the owner-side private file. Outside a job, use `client=` for mock testing.
5. Validate permission rules and explain nearest-`syft.pub.yaml` behavior before changing ACLs.

Read [references/dataset-workflows.md](references/dataset-workflows.md), [references/permissions-reference.md](references/permissions-reference.md), [references/data-formats.md](references/data-formats.md), [references/api-reference.md](references/api-reference.md), and [references/troubleshooting.md](references/troubleshooting.md).

Helpers: [scripts/create_dataset_fixture.py](scripts/create_dataset_fixture.py) creates tiny mock/private fixtures; [scripts/check_permission_yaml.py](scripts/check_permission_yaml.py) checks a simple local ACL rule.
