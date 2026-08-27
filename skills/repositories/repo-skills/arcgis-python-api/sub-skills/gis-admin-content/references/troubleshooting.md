# Troubleshooting

## 1. No credentials or wrong connection mode

### Symptoms

- `GIS()` opens an anonymous session and content creation fails.
- The target portal accepts the URL but returns a read-only or unauthenticated context.
- `gis.properties.user` is missing or not the expected account.
- `gis.users.me` is `None` or points to the wrong identity.

### Checks

- confirm whether the task is read-only or admin/mutation work
- confirm the portal URL and whether it is ArcGIS Online or Enterprise
- confirm the user is signed in with the intended profile or account
- confirm whether the portal expects built-in, enterprise, PKI, OAuth, or ArcGIS Pro active-portal login

### Safe response

If credentials are missing, stop at a plan or dry-run inventory. Do not guess at the password or request that the user paste secrets into the conversation.

## 2. Profile failures and keyring issues

### Symptoms

- `GIS(profile=...)` fails because the profile does not exist
- the profile loads but the stored password is unavailable
- Linux keyring or dbus support is missing
- the stored login points to a different portal than expected

### Checks

- verify the exact profile name
- recreate the profile if the portal URL or username changed
- ensure the OS password manager or keyring backend is available
- on Linux, confirm the Python runtime can access the needed secret-storage backend

### Recovery pattern

- create a fresh profile with explicit `url`, `username`, and `password`
- test the profile with a read-only call before attempting mutation
- keep separate profiles for source and target portals

## 3. SSL, certificate, and `verify_cert` problems

### Symptoms

- TLS handshake errors
- self-signed certificate warnings
- connection succeeds only when certificate validation is disabled
- PKI login fails before the portal is reached

### Checks

- verify whether the portal certificate chain is trusted
- confirm the key/cert or PFX file path exists and matches the portal
- confirm the certificate password if a PFX file is used
- do not leave `verify_cert=False` on a production workflow

### Safe response

Use `verify_cert=False` only as a temporary diagnostic against a known test endpoint. Document the risk and re-enable validation after the issue is isolated.

## 4. OAuth, ArcGIS Pro, and identity-provider edge cases

### Symptoms

- `client_id` login never completes
- `GIS('pro')` cannot find the active portal
- IWA/NTLM/Kerberos login behaves differently from the notebook example
- the portal expects a domain-qualified username

### Checks

- confirm the application registration and client id
- confirm ArcGIS Pro is installed and signed in if using `GIS('pro')`
- confirm whether the identity provider is built-in, LDAP, Active Directory, PKI, or IWA
- on Windows, confirm any required Windows-auth packages are available when using IWA

## 5. Content search and add failures

### Symptoms

- search returns no items
- `get(itemid)` returns `None`
- add or publish fails with a type mismatch or missing file
- empty service creation fails because the service name already exists

### Checks

- verify the exact owner, title, tags, and item type
- check whether the item is already in a folder rather than the root
- verify the data file path or item payload type
- verify service naming conflicts and sharing policy

### Safe response

Prefer search-first inventory and add only after the intended target item, folder, and owner are confirmed.

## 6. Update, protect, share, or delete failures

### Symptoms

- `update()` does not change the item
- `protect(True)` blocks later delete or transfer
- `share(...)` fails because the group is not accessible in the target portal
- `delete()` fails because the item has dependencies or insufficient permissions

### Checks

- confirm you are acting on the correct item id
- confirm the item is not protected before deletion or reassignment
- inspect resources and related items
- confirm group titles/ids belong to the same portal
- verify the caller owns the item or has admin privileges

### Recovery pattern

1. record the original item state
2. unprotect only if needed
3. remove or reassign dependents
4. retry the mutation once
5. if the attempt partially succeeded, reconcile the new item ids before trying again

## 7. Resource-related failures

### Symptoms

- missing thumbnail, metadata, or config file
- resource list exists but download or export fails
- an item update breaks a companion HTML/JSON file

### Checks

- list item resources before mutation
- export critical resources as part of the backup plan
- keep a copy of configuration resources before updating app-like items

## 8. User and group lifecycle failures

### Symptoms

- `users.create(...)` fails because the username already exists
- a user cannot be deleted because content or groups still depend on them
- a group cannot be created or deleted due to role or membership constraints
- `add_users(...)` or `remove_users(...)` reports partial membership changes

### Checks

- verify the role, provider, and user type
- reassign or delete content before removing the user
- remove or reassign group ownership before deleting the group
- keep system accounts out of automated delete loops

### Safe response

Treat user and group deletion as a multi-step workflow, not a single call.

## 9. Admin server and datastore failures

### Symptoms

- server validation fails
- a service cannot be stopped or deleted
- datastore validation fails
- publishing a service errors out during admin work

### Checks

- list and validate the federated servers first
- confirm the service type and folder
- check whether the service is system-managed and should be preserved
- confirm the caller has server administrator privileges

### Safe response

Do not delete or rename services until you know whether the service is portal-managed, system-managed, or a preserved utility service.

## 10. Collaboration and portal migration failures

### Symptoms

- collaboration invitation/response files cannot be imported
- guest and host portals disagree on workspace ids
- sync or schedule operations fail after a migration

### Checks

- confirm host/guest roles and workspace ids
- confirm the invitation and response files match the current portals
- confirm the group attached to the collaboration exists in both portals
- keep collaboration files private and short-lived

## 11. Cloning and offline backup failures

### Symptoms

- cloned items still point back to the source service
- users or groups are copied but content relationships are missing
- offline import stops halfway and leaves a partially imported package
- source and target portals contain conflicting names or ids

### Checks

- inventory source dependencies before cloning
- build owner and group mappings first
- confirm which item types are supported for cloning
- set `search_existing_items` and `preserve_item_id` only when the target portal can safely accept them
- use rollback-friendly import options for offline packages

### Recovery pattern

- validate the target clone before deleting the source copy
- keep a mapping of source ids to target ids
- reconcile relationships and sharing after the bulk copy
- if the package must be atomic, require rollback on failure

## 12. Safe refusal patterns for the generated skill

The generated skill should refuse or defer when:

- credentials are missing
- the portal identity is not known
- the user asks for a destructive action without a backup or confirmation plan
- the task requires a portal admin role the caller has not established
- the user asks to run an upstream cleanup or clone script directly

In those cases, return a minimal plan, a list of required inputs, or a safe diagnostic sequence instead of a runnable destructive command.
