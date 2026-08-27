# Object Stores and File Sources

Galaxy separates raw user-visible files from Galaxy-managed datasets. File sources let users browse or import files. Object stores hold Galaxy datasets after upload, tool execution, library import, or object-store selection. Storage changes are deployment-sensitive because they can affect persistence, privacy, quotas, credentials, and cleanup semantics.

## Object Store Configuration

Global object stores are configured through the object-store config file or embedded object-store config in Galaxy’s main configuration. Common backends include disk, distributed, hierarchical, S3-compatible, Azure Blob, iRODS, Rucio, Onedata, Pulsar, and related caching variants.

Review an object-store change for:

- Backend type and whether optional dependencies are installed.
- Stable object-store IDs when data already exists.
- `private` behavior and security expectations for shared datasets.
- Cache path, cache size, staging path, and remote-size behavior for remote stores.
- `store_by` strategy and whether tests assume UUID-based paths.
- Distributed/hierarchical weighting and selection behavior.
- Quota and badges such as slower, less stable, cloud, private, or not backed up.

Object-store selection for users requires a distributed primary object store. If the primary store is simple disk, hierarchical, or another non-distributed layout, user-defined object-store templates are not the right lever.

## Object Store Templates

Object-store templates let admins expose user-instantiable storage options. Template libraries are YAML lists with IDs, names, descriptions, variables, secrets, optional environment/admin secrets, and a `configuration` block that expands into a concrete object-store configuration.

Safe template patterns:

- Put credentials in `secrets` or Vault-backed admin/environment values, never in plain examples.
- Use validation constraints and path-component types/filters for user-supplied path fragments.
- Keep admin-supplied environment values distinct from per-user secrets.
- Use modern `boto3` S3-compatible templates unless maintaining legacy `aws_s3` or `generic_s3` behavior is intentional.
- Validate examples with template model tests before trying remote credentials.

## File Sources

File sources expose raw files through URI roots such as local POSIX, FTP, S3FS, Azure, WebDAV, Dropbox, OneDrive, Google Drive, iRODS, HTTP, DRS, Zenodo, InvenioRDM, and other plugins. They may be global, stock, or user-defined through templates.

Review a file-source change for:

- `id`, `type`, URI root, browsing capability, writing capability, and role/group restrictions.
- Symlink security for POSIX sources and explicit allowlists when following links is required.
- `writable` behavior and parent-directory creation settings.
- Whether stock FTP/import sources purge or preserve imported files.
- OAuth2 behavior: server-side client credentials and user refresh tokens must not be exposed to jobs or logs.
- Cloud/network tests that depend on environment variables or external accounts.

Galaxy includes a file-source validation script in the codebase that instantiates configured file sources, but this generated skill does not bundle it because it imports live Galaxy internals and depends on the target installation. Prefer adapting its read-only validation pattern inside the user’s checkout when requested.

## Test Strategy

Start with the safest local checks:

- Template model/unit tests for object-store and file-source template libraries.
- Local disk, distributed disk, POSIX, memory, base64, and temp file-source tests.
- Serialization tests for user object stores and user file sources.
- Path traversal and symlink-security tests for POSIX sources.

Escalate only when explicitly authorized:

- Cloud object-store tests requiring `GALAXY_TEST_AWS_*`, `GALAXY_TEST_AZURE_*`, Google interop, or similar variables.
- File-source tests requiring Dropbox, OneDrive, Google Drive, BaseSpace, Onedata, iRODS, Azure, WebDAV, or other external credentials.
- Integration object-store tests that start or contact MinIO, iRODS, Rucio, Onedata, Swift, or Azure services.

When credentials are absent, record a skip reason such as “requires cloud credentials and disposable bucket/container” rather than weakening assertions.

## Source Script Inventory

Galaxy’s object-store and cleanup scripts are reference-only for this skill:

- Object-store migration/copy scripts can connect to databases and remote storage, update dataset records, and remove source files after successful copy. Do not bundle or run them without an explicit migration plan.
- Cleanup dataset scripts can mark histories, libraries, folders, dataset instances, datasets, and metadata files as deleted or purged; some modes remove files from disk. Do not bundle or run them as generic helpers.
- Shell wrappers around cleanup modes are destructive operational shortcuts. Treat them as excluded runtime content.

For storage maintenance, ask the user for the target deployment, backup status, exact IDs/scope, dry-run output, and rollback plan before suggesting any write action.
