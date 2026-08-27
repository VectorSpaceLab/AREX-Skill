# Auth and RBAC

## Auth modes

Feast server auth is selected from `feature_store.yaml` through `auth.type`:

```yaml
auth:
  type: no_auth
```

Supported server auth manager types are:

- `no_auth`: default/backward-compatible behavior; servers install an allow-all manager and skip security-manager enforcement.
- `oidc`: REST, gRPC, and Arrow servers extract bearer tokens and parse OIDC claims using the configured OIDC auth config.
- `kubernetes`: servers extract Kubernetes tokens and derive user, group, namespace, and role facts.

Server initialization uses a protocol-specific token extractor:

| Server | Protocol path | Token source |
|---|---|---|
| Feature server | REST/FastAPI | HTTP authorization headers |
| Registry server | gRPC | gRPC metadata |
| Offline server | Arrow Flight | Arrow Flight middleware metadata |

## Token patterns

REST feature-server call:

```bash
curl -sS -X POST http://localhost:6566/get-online-features \
  -H "Authorization: Bearer ${FEAST_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"features":["driver_hourly_stats:conv_rate"],"entities":{"driver_id":[1001]}}'
```

Python REST client pattern:

```python
import requests

response = requests.post(
    "http://localhost:6566/get-online-features",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "features": ["driver_hourly_stats:conv_rate"],
        "entities": {"driver_id": [1001]},
    },
)
response.raise_for_status()
```

gRPC metadata pattern:

```python
metadata = [("authorization", f"Bearer {token}")]
# Pass metadata=metadata to the generated Feast registry or serving gRPC stub call.
```

CLI/SDK Kubernetes token provisioning options:

```bash
export LOCAL_K8S_TOKEN="<token>"
feast get-online-features --features driver_hourly_stats:conv_rate --entity-rows '{"driver_id": 1001}'
```

```yaml
auth:
  type: kubernetes
  user_token: "<token>"
```

Token resolution priority observed in the user-token guide: service-to-service `INTRA_COMMUNICATION_BASE64`, direct config `user_token`, pod service-account token, then `LOCAL_K8S_TOKEN`.

## RBAC concepts

Feast RBAC secures resources with permissions made of:

- Resource types: Feast objects such as projects, data sources, feature views, on-demand feature views, feature services, entities, and permissions.
- Actions: logical operations including `DESCRIBE`, create/update/delete, `READ_ONLINE`, `WRITE_ONLINE`, `QUERY_OFFLINE`, and `WRITE_OFFLINE`.
- Policies: role-, group-, namespace-, or combined group/namespace-based checks.

Example policy objects for feature-definition authors:

```python
from feast.feast_object import ALL_RESOURCE_TYPES
from feast.permissions.action import READ, ALL_ACTIONS, AuthzedAction
from feast.permissions.permission import Permission
from feast.permissions.policy import RoleBasedPolicy, GroupBasedPolicy

reader = Permission(
    name="reader_permission",
    types=ALL_RESOURCE_TYPES,
    policy=RoleBasedPolicy(roles=["reader"]),
    actions=[AuthzedAction.DESCRIBE] + READ,
)

data_team = Permission(
    name="data_team_permission",
    types=ALL_RESOURCE_TYPES,
    policy=GroupBasedPolicy(groups=["data-team"]),
    actions=ALL_ACTIONS,
)
```

Route object modeling and where to place `Permission` instances to `../../feature-definitions/SKILL.md`. Route applying those objects with `feast apply` to `../../feature-repos-and-cli/SKILL.md`.

## Action checks by route

Feature-server behavior includes these authorization checks:

- `/get-online-features`: checks `READ_ONLINE` on the requested `FeatureService`, feature views, and on-demand feature views when auth is active.
- `/retrieve-online-documents`: uses the same feature resolution and online-read permission path as online feature retrieval.
- `/push`: checks `WRITE_ONLINE`, `WRITE_OFFLINE`, or both depending on `to: online`, `offline`, or `online_and_offline`.
- `/write-to-online-store`: checks `WRITE_ONLINE` on the target feature view.
- `/materialize` and `/materialize-incremental`: check `WRITE_ONLINE` on selected or materializable feature views.

Offline-server behavior checks offline actions such as query, validation, persist, and write paths against feature views, feature services, data sources, and saved dataset resources.

Registry-server behavior checks `DESCRIBE`, create/update/delete, and permission update operations around registry object APIs.

## Kubernetes RBAC alignment

For `auth.type: kubernetes`, align Feast permissions with Kubernetes identities:

- Role policies require Kubernetes RBAC `Role` names that match Feast `RoleBasedPolicy.roles` values.
- The matching Kubernetes `Role` should live in the namespace of the Feast service.
- Client pods may use their own service accounts in different namespaces, but the `RoleBinding` connecting them to the service namespace role must exist in the Feast service namespace.
- Group and namespace policies require the token to expose the expected groups or namespaces.

## Diagnosing 401/403 versus missing feature objects

Use this decision path when a user reports a failed server call:

1. Check status and body. A 401-style failure usually means no token, malformed bearer header, expired token, or token parser/config failure.
2. A 403-style failure or permission-denied message means auth succeeded but the user lacks the action for the requested resource.
3. A Feast object error such as missing feature view, feature service, entity, or feature ref means routing reached Feast logic but the requested object is absent, not applied, hidden by project mismatch, or misnamed.
4. If one user can call `/health` or list metadata but cannot retrieve features, suspect missing `READ_ONLINE`, `QUERY_OFFLINE`, `WRITE_ONLINE`, or `WRITE_OFFLINE`, not network failure.
5. If a request works with `auth.type: no_auth` but fails with OIDC/Kubernetes, keep server topology and feature refs fixed while narrowing token claims and permissions.

RBAC demo expectations show useful mental models: a read-only role may pass basic validation/DESCRIBE but be denied historical, materialization, online, and push; a batch admin may run historical queries but be denied materialization/online; a store admin should pass all.

## Secure handling checklist

- Do not embed long-lived tokens in public skill files, scripts, or committed config examples.
- Prefer environment variables or mounted secret files for tokens and certificates.
- For self-signed TLS, configure `cert` or `FEAST_CA_CERT_FILE_PATH`; do not disable verification in production clients.
- Keep server-to-server authentication separate from end-user tokens when using `INTRA_COMMUNICATION_BASE64`.
- Confirm permission objects are applied before debugging client tokens.
