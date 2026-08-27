# Ingress and routing

This reference covers LeptonAI ingress resources, canary endpoint routing, and access-control facts that affect endpoint/ingress exposure. It does not cover endpoint deployment itself; route workload creation and update mechanics to `workload-management`.

## Ingress lifecycle commands

| Goal | CLI pattern | Behavior |
|---|---|---|
| List ingresses | `lep ingress list` | Prints name, creation time, domain name, and status message for each ingress. |
| Create an ingress | `lep ingress create -d DOMAIN_NAME` | Creates an ingress with `spec.domain_name=DOMAIN_NAME` and no endpoint list by default. |
| Get ingress details | `lep ingress get -n INGRESS_NAME` | Prints the ingress object as JSON using safe serialization. Use this before mutating endpoints. |
| Delete an ingress | `lep ingress delete -n INGRESS_NAME` | Deletes the named ingress. This is destructive and requires explicit confirmation. |

An ingress name used by `-n/--name` is the identifier accepted by the API route. The `create` command asks for a domain name (`-d/--domain-name`); depending on server behavior, the returned metadata determines the subsequent name.

## Endpoint routing commands

| Goal | CLI pattern | Behavior | Safe use |
|---|---|---|---|
| Add one endpoint | `lep ingress add-endpoint -n INGRESS --endpoint ENDPOINT -w WEIGHT` | Reads the ingress, refuses to duplicate an existing endpoint, appends a `LeptonIngressEndpoint`, patches the ingress, and prints the traffic distribution. Default weight is `100`. | Use for incremental canary introduction. |
| Update one endpoint weight | `lep ingress update-endpoint -n INGRESS --endpoint ENDPOINT -w WEIGHT` | Reads the ingress, finds the endpoint, changes only its weight, patches the ingress, and prints the distribution. | Use when all endpoints should remain present. |
| Remove one endpoint | `lep ingress remove-endpoint -n INGRESS --endpoint ENDPOINT` | Reads the ingress, errors if no endpoints or missing endpoint, then calls the dedicated endpoint deletion API. | Confirm because traffic shifts away from that endpoint. |
| Replace all endpoints | `lep ingress set-endpoints -n INGRESS -e ENDPOINT:WEIGHT ...` | Parses a complete endpoint list, validates non-negative weights and total weight greater than zero, then replaces `spec.endpoints` on the ingress. | Treat as destructive: every omitted endpoint is removed. |

`set-endpoints` accepts repeated `-e/--endpoints` values in `endpoint:weight` format. It uses integer weights, rejects negative weights, and rejects a total weight of zero. Use the bundled preflight script to detect omitted existing endpoints before presenting a `set-endpoints` command.

## Canary weight semantics

Ingress weights are relative. The percentage for an endpoint is:

```text
endpoint_weight / sum(all_endpoint_weights) * 100
```

Equivalent examples:

| Endpoint weights | Result |
|---|---|
| `stable:80`, `canary:20` | stable 80%, canary 20% |
| `stable:8`, `canary:2` | stable 80%, canary 20% |
| `stable:1`, `canary:1` | 50/50 split |
| `stable:90`, `canary:10` | stable 90%, canary 10% |

Safe rollout pattern:

```bash
# Read current state first
lep ingress get -n api.example.com

# Add canary incrementally; existing endpoints remain
lep ingress add-endpoint -n api.example.com --endpoint canary-v2 -w 10

# Adjust only the canary weight; existing endpoints remain
lep ingress update-endpoint -n api.example.com --endpoint canary-v2 -w 25

# Replace all endpoints only after listing every endpoint intentionally
lep ingress set-endpoints -n api.example.com \
  -e stable-v1:75 \
  -e canary-v2:25
```

Rollback choices:

- If only one canary endpoint was added, use `remove-endpoint` to remove that endpoint and keep the rest.
- If a complete replacement was already applied, use `set-endpoints` again with the complete desired stable list. Do not provide only one endpoint unless the user wants all others removed.

## Ingress API surface

`APIClient().ingress` exposes live workspace methods:

| API method | Purpose |
|---|---|
| `list_all()` | `GET /ingress`; returns ingress objects. |
| `create(lepton_ingress)` | `POST /ingress`; create from `LeptonIngress(metadata=..., spec=...)`. |
| `get(name_or_ingress)` | `GET /ingress/{name}`; returns one ingress. |
| `delete(name_or_ingress)` | `DELETE /ingress/{name}`. |
| `update(name_or_ingress, spec)` | `PATCH /ingress/{name}` with the serialized ingress object. |
| `create_endpoint(name_or_ingress, endpoint_spec)` | `POST /ingress/{name}/endpoint/deployment`; create an endpoint route. |
| `delete_endpoint(name_or_ingress, name_or_deployment)` | `DELETE /ingress/{name}/endpoint/deployment/{deployment}`; remove one endpoint route. |

The CLI currently uses full ingress patching for add/update/set and the dedicated delete-endpoint API for removal.

## Endpoint access-control interplay

Access-control flags are endpoint create/update concerns, so route actual endpoint mutations to `workload-management`. When reviewing a plan, enforce these facts:

| Flag combination | Network/IP access | Token behavior | Notes |
|---|---|---|---|
| `--public` | Clears IP restrictions by setting an empty allowlist. | With no tokens, produces no token requirement. With `--tokens`, tokens are still required. | `--public --tokens` means public network reachability plus token authentication. |
| `--ip-whitelist A --ip-whitelist B,C` | Restricts access to the parsed individual IP/CIDR values. | Tokens are independent; specify tokens explicitly when authentication is required. | `--public` and `--ip-whitelist` are mutually exclusive. |
| `--tokens TOKEN ...` | Does not by itself restrict source IPs. | Rebuilds the endpoint token list from the supplied literal tokens on create; on update it replaces tokens only when provided. | Redact token values in all output. |
| No `--public`, no `--ip-whitelist`, no `--tokens` on create | Current CLI code warns that the endpoint is publicly accessible without tokens. | Empty token list. | Do not rely on implicit defaults for production; ask for an explicit access mode. |
| `--visibility private` | Controls who can view the endpoint resource metadata. | Does not replace `--tokens` or `--ip-whitelist` access control. | Route to workload-management for endpoint command construction. |

If you see older examples that imply a workspace-token default for private endpoints, verify against the installed CLI before relying on that behavior. The current source separates IP allowlisting from token authentication and does not make tokens appear from IP allowlisting alone.

## IP allowlist parsing

`--ip-whitelist` accepts both repeated values and comma-separated values. Whitespace around comma-separated entries is stripped; empty entries are ignored.

```bash
--ip-whitelist 203.0.113.0/24 --ip-whitelist 198.51.100.10
--ip-whitelist "203.0.113.0/24, 198.51.100.10"
```

The flag rejects option-like missing values such as `--ip-whitelist --tokens X` and reports that `--ip-whitelist` requires an argument.

## Preflight before ingress mutation

1. Ask for or run an authorized `lep ingress get -n INGRESS` to capture the current endpoint list.
2. For `set-endpoints`, compare the current list with the proposed list. Any current endpoint not listed will be removed.
3. Use nonzero total weights and non-negative individual weights.
4. Confirm the final distribution in percentages and the exact command.
5. After authorized execution, read back with `lep ingress get -n INGRESS` or `lep ingress list` and compare expected endpoint names and relative weights.
