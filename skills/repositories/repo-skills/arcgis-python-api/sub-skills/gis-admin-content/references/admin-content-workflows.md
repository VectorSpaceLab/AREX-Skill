# Admin and content workflows

## Scope

This reference covers safe operating patterns for:

- connecting to ArcGIS Online or ArcGIS Enterprise with `GIS`
- inventorying, creating, updating, sharing, protecting, exporting, deleting, and cloning content
- working with item resources, ownership, folders, and item relationships
- creating, searching, updating, and deleting users and groups
- reading and adjusting organization admin settings such as licenses, credits, UX, federated servers, and collaborations
- performing offline content export/import and portal migration planning
- recognizing when source portal scripts are reference-only and should not be bundled as runtime helpers

## Preflight checklist

Before any mutation:

1. Identify the target portal, org role, and whether the task is read-only, reversible, or destructive.
2. Decide which connection mode is appropriate: anonymous, active profile, built-in credentials, OAuth, PKI, or active portal.
3. Confirm the authenticated identity with `gis.properties.user`, the org/portal name, and the user role.
4. Confirm that the caller has the required privileges for the action.
5. Inventory what will change:
   - content items and folders
   - item resources and related items
   - users and groups
   - credits, licenses, servers, collaboration workspaces, or backups
6. Capture a rollback plan:
   - item exports or downloads
   - resource exports
   - folder/owner maps
   - group membership/sharing state
   - offline package export if appropriate
7. For destructive actions, require explicit confirmation and a bounded target list.

## Connection modes

### Anonymous read-only access

Use `GIS()` or `GIS(url)` with no username/password/profile when the task only needs public access.

Good for:

- reading public items and portals
- testing module import and object construction
- checking shared content without mutation

Not good for:

- content creation
- ownership changes
- group membership changes
- server/admin/collaboration actions

### Built-in account or enterprise account

Use `GIS(url, username, password)` for built-in portal accounts, LDAP-backed accounts, or Active Directory accounts when the portal expects username/password login.

Guidance:

- prefer secret input over literal passwords in notebooks or scripts
- use domain-qualified usernames only when the portal requires them
- confirm whether the portal treats the account as built-in or enterprise-backed before trying admin-only operations

### Persistent profile

Use `GIS(..., profile="name")` to store connection details in a local profile and reuse them later with `GIS(profile="name")`.

Use this when:

- the user signs into the same portal repeatedly
- the workflow needs a non-interactive script without retyping credentials
- the task must switch between more than one portal safely

Remember:

- the profile stores non-password fields in a local config file
- the password is kept in the OS password manager when supported
- Linux may need keyring/secret-service support configured

### PKI / client certificate

Use certificate-based login when the portal is protected by PKI.

Patterns:

- `key_file` + `cert_file` for a PEM key/cert pair
- `cert_file` with a PKCS12/PFX file and password when the portal expects a bundled client certificate

Rules:

- never commit or echo certificate passwords
- validate certificate paths before attempting the connection
- use `verify_cert=True` unless the target is a known test system and the user accepts the risk

### OAuth / client id

When the portal uses app-based login, the constructor accepts `client_id`.

Use this only when the workflow is explicitly app-authenticated and the user can provide the app registration details.

### ArcGIS Pro active portal

`GIS('pro')` is useful when the active portal in ArcGIS Pro should be reused without retyping credentials.

Use it only when the user confirms that ArcGIS Pro is installed, signed in, and running in the right account context.

## Safe content workflow

### Search and inspect

Use search before mutation:

- `gis.content.search(...)` for standard inventory
- `gis.content.advanced_search(...)` for counts, sorting, and broader queries
- `gis.content.get(itemid)` for a known item id
- `user.items(...)` and `user.folders` for ownership views

Typical preflight checks:

- exact owner
- item type
- item count
- sharing state
- folder location
- dependent or related items
- item resources and metadata

### Add and publish

Common patterns:

- `gis.content.add(item_properties, data=...)` for content upload
- `folder.add(...)` when the item should land in a specific folder
- `item.publish(...)` to publish a hosted item after upload
- `gis.content.create_service(...)` only when an empty hosted service is intended and the org allows it

Check before publishing:

- whether the item type is publishable
- whether the service name already exists
- whether the operation will create a hosted service or consume credits
- whether the target owner/folder is correct
- whether the output should be shared immediately or kept private

### Update and protect

Use `item.update(...)` for metadata, data, thumbnail, or metadata file changes.

Use `item.protect(True)` before risky work such as migrations or ownership changes. Clear protection only when the item is ready for the next step.

### Share and unshare

Use `item.share(everyone=..., org=..., groups=...)` with care.

Recommendations:

- share after the item is validated, not before
- record the original sharing state before cloning or reassignment
- when sharing to groups, confirm the group ids/titles belong to the target portal

### Delete safely

Deletion should be the last step.

Checklist:

- confirm the item is not protected
- confirm the item has no required dependents
- check related items and resource dependencies
- confirm the owner and folder
- prefer a dry-run or inventory-first pass if available
- remove or reassign dependent items before deleting the parent

Use `dry_run` or `force`/`permanent` only when the user explicitly wants the destructive path and the implications are understood.

### Ownership, folders, and relationships

Use these operations when moving content:

- `item.reassign_to(target_owner, target_folder=...)`
- `item.move(folder)`
- `gis.content.create_folder(...)`
- `gis.content.delete_folder(...)`
- `item.related_items(...)`
- `item.add_relationship(...)`
- `item.delete_relationship(...)`

Safer migration order:

1. create or verify the target owner and folder
2. clone or add the item
3. recreate sharing and relationships
4. validate the result
5. only then retire the source copy if needed

## Item resources

Item resources are separate from the item payload and often hold configuration files, thumbnails, JSON, HTML fragments, or other auxiliary files.

Use:

- `item.resources.list()` to inspect resource names
- `item.resources.get(...)` to download a resource
- `item.resources.add(...)` or `update(...)` to replace or add resource content
- `item.resources.export(...)` to export the whole set when supported

Treat resources as part of the rollback plan for app or configuration items.

## Users and groups

### Users

Use `gis.users.search(...)`, `gis.users.get(...)`, and `gis.users.create(...)` to manage accounts.

Before creating or deleting users:

- verify the portal mode and account provider
- check for duplicate usernames
- confirm the role and user type
- decide whether existing content must be reassigned first

Common safe sequence for user removal:

1. reassign or export their content
2. remove or reassign group ownership
3. validate that server-side services or collaborations do not still depend on the user
4. delete the user only when all dependencies are cleared

### Groups

Use `gis.groups.search(...)`, `gis.groups.get(...)`, `gis.groups.create(...)`, and `gis.groups.create_from_dict(...)`.

For membership changes:

- `group.add_users(...)`
- `group.remove_users(...)`
- `group.get_members()`
- `group.content()` to inspect shared items
- `group.reassign_to(...)` when ownership changes are required

Before deleting a group:

- check the owner
- check current members
- check the items shared to the group
- confirm that the target portal has an equivalent group if this is a clone or migration

## Organization admin, credits, licenses, and UX

Common admin surfaces used in the guides and samples:

- `gis.admin.credits`
- `gis.admin.license`
- `gis.admin.servers`
- `gis.admin.collaborations`
- organization UX/branding settings
- location tracking and other org policy controls when present

Guidance:

- read licenses and credit budgets before assigning or revoking anything
- record the original credit limits before changing them
- validate branding/UX settings with a non-destructive read before updating banners, logos, or names
- avoid accidental credit spending by checking whether the action publishes a hosted service or runs a service-backed job

## Servers and datastore operations

Use server/admin operations only when the caller is a verified administrator and the target server is known.

Safe sequence:

1. list federated servers
2. validate the server connection
3. inspect service folders and service types
4. confirm which services are managed by the portal versus system-preserved
5. stop, rename, publish, or delete services only after explicit confirmation

For datastores, validate the datastore object before update or removal.

## Collaborations

Use collaboration operations when the task explicitly involves distributed GIS workspaces.

Typical flow:

- host creates the collaboration and workspace
- host sends invitation
- guest accepts the invitation
- the group is attached to the collaboration
- schedules and sync are managed only after both portals confirm the workspace exists

Keep invitation and response files private and disposable.

## Cloning and migration

### Item cloning

Prefer `gis.content.clone_items(...)` for supported portal-to-portal content clones.

Useful options:

- `copy_data`
- `copy_global_ids`
- `search_existing_items`
- `item_mapping`
- `group_mapping`
- `owner`
- `preserve_item_id`
- `export_service`
- `preserve_editing_info`

Cloning preflight:

- verify source and target portal identities
- inventory all source dependencies
- check which items are web layers, maps, packages, or app items
- identify all groups that receive shared items
- confirm the target has matching accounts or a deliberate owner mapping
- confirm service/credit capacity

### Portal shell clones and offline backups

Use manual user/group/content cloning or offline export/import when a full portal shell or air-gapped move is required.

Important caveats:

- service URLs may still point back to the source unless the workflow explicitly republished them
- not every item type is safe or supported for direct clone/import
- relationships and sharing often need a second pass
- cross-organization account creation and cleanup must be planned first

### Offline content backup

Use `gis.content.offline.export_items(...)` and `gis.content.offline.import_content(...)` for package-based export/import workflows.

Guidance:

- export only the items needed for the recovery plan
- keep the package path and target folder explicit
- use `failure_rollback=True` when importing a multi-item package that must remain atomic
- preserve ids only when the target org can safely accept them

## Source-script safety notes

The following upstream samples are reference-only and should not be bundled as runtime helper scripts:

- `cleanup.py`, `create_groups.py`, `create_users.py`, and `publish_content.py`
- `clone_portal.py` for users, groups, content, and relationships
- `CloneUsersGroupsSharingshell.py`, a legacy shell clone sample with hard-coded internal endpoints and secrets
- `misc/setup.py`, `misc/teardown.py`, and `misc/_common.py`, which delete users, groups, items, services, or tracking configuration

During offline verification of this generated skill, a parser help path may be inspected only for argument shape. Future runtime workflows should use the distilled guidance here instead of depending on the original source sample files. Never let the mutating branch run in a generated runtime helper.

Why they are excluded:

- they require live credentials and privileged portals
- they mutate or delete production content
- some contain hard-coded sample credentials or local machine paths
- some are not idempotent and can leave partial state if interrupted

Use them only as workflow evidence for safe, user-facing guidance.
