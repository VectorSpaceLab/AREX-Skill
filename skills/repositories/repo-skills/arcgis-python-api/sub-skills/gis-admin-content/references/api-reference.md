# Verified API reference

## Verification baseline

- Installed package evidence for this skill tree: `arcgis 2.4.1.3` and `arcgis-mapping 4.31.0`.
- Base imports for the ArcGIS package family were confirmed in the inspection environment.
- Optional surfaces such as deep learning, dashboards, and AI services are version- or dependency-sensitive and may be absent in the current environment.
- No live portal, service, or destructive admin calls were executed while constructing this reference.

## Core constructor signatures

### `arcgis.gis.GIS`

```python
GIS(url=None, username=None, password=None, key_file=None, cert_file=None,
    verify_cert=True, set_active=True, client_id=None, profile=None, **kwargs)
```

Verified meaning from the installed docstring: the object represents a single ArcGIS Online organization or ArcGIS Enterprise deployment and provides helper objects for content, users, and groups.

Key usage notes:

- `url=None` with no auth parameters defaults to ArcGIS Online behavior.
- `profile` reuses stored login material.
- `verify_cert` defaults to `True`.
- `key_file` and `cert_file` support certificate-based login.
- `client_id` supports OAuth-style app login.
- `set_active` controls whether the instance becomes the active GIS object.

### `arcgis.gis.Item`

```python
Item(gis, itemid, itemdict=None)
```

Verified meaning from the installed docstring: an item is a unit of content in the GIS and may expose item data and resources.

## GIS object surfaces

The installed `arcgis.gis` module exports the expected GIS administration and content objects, including:

- `GIS`
- `ContentManager`
- `UserManager`
- `GroupManager`
- `OfflineContentManager`
- `ResourceManager`
- `User`
- `Group`
- `Item`
- `RoleManager`
- `LicenseManager`
- `CreditManager`
- `ServerManager`
- `Datastore`
- `OfflineContentManager`
- collaboration classes

## Content manager patterns

### `search`

```python
gis.content.search(query, item_type=None, sort_field='avgRating', sort_order='desc',
                   max_items=10, outside_org=False, categories=None,
                   category_filters=None, enrich=None, filter=None)
```

Use for general item lookup. Good preflight filters include owner, title, type, tags, and group-related content discovery.

### `advanced_search`

```python
gis.content.advanced_search(query, return_count=False, max_items=100, bbox=None,
                            categories=None, category_filter=None, start=1,
                            sort_field='title', sort_order='asc', count_fields=None,
                            count_size=None, as_dict=False, enrich=False, filter=None)
```

Use when you need counts, sorted inventory, or a larger portal-wide catalog pass.

### `get`

```python
gis.content.get(itemid)
```

Use when the item id is already known.

### `add`

```python
gis.content.add(item_properties, data=None, thumbnail=None, metadata=None,
                owner=None, folder=None, item_id=None, **kwargs)
```

Use for uploading content into the portal. The owner and folder can be set explicitly.

### `create_service`

```python
gis.content.create_service(name, service_description='', has_static_data=False,
                           max_record_count=1000, supported_query_formats='JSON',
                           capabilities=None, description='', copyright_text='',
                           wkid=102100, create_params=None, service_type='featureService',
                           owner=None, folder=None, item_properties=None, is_view=False,
                           tags=None, snippet=None, item_id=None)
```

Use only when the task truly needs a new hosted service.

### `clone_items`

```python
gis.content.clone_items(items, folder=None, item_extent=None, use_org_basemap=False,
                        copy_data=True, copy_global_ids=False, search_existing_items=True,
                        item_mapping=None, group_mapping=None, owner=None,
                        preserve_item_id=False, export_service=False,
                        preserve_editing_info=False, **kwargs)
```

Use for supported portal-to-portal cloning workflows.

### Folder helpers

```python
gis.content.create_folder(folder, owner=None)
gis.content.delete_folder(folder, owner=None)
```

### Offline content manager

```python
gis.content.offline.export_items(items, output_folder=None, package_name=None,
                                 service_format='File Geodatabase')
gis.content.offline.list_items(package_path)
gis.content.offline.import_content(package_path, item_ids=[], preserve_ids=False,
                                   folder=None, failure_rollback=False)
```

## Item patterns

### Update, publish, protect, share, delete

```python
item.update(item_properties=None, data=None, thumbnail=None, metadata=None)
item.publish(publish_parameters=None, address_fields=None, output_type=None,
             overwrite=False, file_type=None, build_initial_cache=False,
             item_id=None, geocode_service=None, future=False)
item.protect(enable=True)
item.share(everyone=False, org=False, groups=None, allow_members_to_edit=False)
item.delete(force=False, dry_run=False, permanent=False)
```

Safe interpretation:

- `update` mutates metadata or data.
- `publish` may create a hosted service and can have billing/credit side effects.
- `protect` should be enabled before risky admin workflows.
- `delete` may support a dry run and can be forced/permanent only when explicitly intended.

### Resources and data

```python
item.download(save_path=None, file_name=None)
item.download_thumbnail(save_folder=None)
item.download_metadata(save_folder=None)
item.get_data(try_json=True)
item.resources.list()
item.resources.get(file, try_json=True, out_folder=None, out_file_name=None)
item.resources.add(file=None, folder_name=None, file_name=None, text=None,
                   archive=False, access=None, properties=None)
item.resources.update(file=None, folder_name=None, file_name=None, text=None,
                      properties=None)
item.resources.export(save_path=None, file_name=None)
```

### Ownership and relationships

```python
item.reassign_to(target_owner, target_folder=None)
item.move(folder)
item.related_items(rel_type, direction='forward')
item.add_relationship(rel_item, rel_type)
item.delete_relationship(rel_item, rel_type)
```

## User manager and user patterns

### Search and create

```python
gis.users.search(query=None, sort_field='username', sort_order='asc', max_users=100,
                 outside_org=False, exclude_system=False, user_type=None, role=None)
gis.users.advanced_search(query, return_count=False, max_users=10, start=1,
                          sort_field='username', sort_order='asc', as_dict=False)
gis.users.get(username, outside_org=True)
gis.users.create(username, password, firstname, lastname, email, role=None,
                 description=None, provider='arcgis', idp_username=None,
                 level=2, thumbnail=None, user_type=None, credits=-1,
                 groups=None, email_text=None)
```

### User object patterns

```python
user.items(folder=None, max_items=100)
user.folders
user.update(access=None, preferred_view=None, description=None, tags=None,
            thumbnail=None, fullname=None, email=None, culture=None,
            region=None, first_name=None, last_name=None, security_question=None,
            security_answer=None, culture_format=None, categories=None)
user.reassign_to(target_username)
user.delete(reassign_to=None)
user.download_thumbnail(save_folder=None)
```

Important:

- delete or reassign content before deleting a user
- do not assume a user can be removed without role or ownership cleanup
- enterprise-backed users may not follow the same password rules as built-in users

## Group manager and group patterns

### Search and create

```python
gis.groups.search(query='', sort_field='title', sort_order='asc', max_groups=1000,
                  outside_org=False, categories=None, filter=None)
gis.groups.get(groupid)
gis.groups.create(title, tags, description=None, snippet=None, access='public',
                  thumbnail=None, is_invitation_only=False, sort_field='avgRating',
                  sort_order='desc', is_view_only=False, auto_join=False,
                  provider_group_name=None, provider=None, max_file_size=None,
                  users_update_items=False, display_settings=None, is_open_data=False,
                  leaving_disallowed=False, hidden_members=False,
                  membership_access=None, autojoin=False)
gis.groups.create_from_dict(dict)
```

### Group object patterns

```python
group.update(title=None, tags=None, description=None, snippet=None, access=None,
             is_invitation_only=None, sort_field=None, sort_order=None,
             is_view_only=None, thumbnail=None, max_file_size=None,
             users_update_items=False, clear_empty_fields=False,
             display_settings=None, is_open_data=False, leaving_disallowed=False,
             member_access=None, hidden_members=False, membership_access=None,
             autojoin=False, **kwargs)
group.add_users(usernames=None, admins=None)
group.remove_users(usernames)
group.get_members()
group.content(max_items=1000)
group.reassign_to(target_owner)
group.delete()
group.invite_users(usernames, role='group_member', expiration=10080)
```

## Admin, license, credit, server, and collaboration patterns

### Credits and licenses

```python
gis.admin.credits.enable()
gis.admin.credits.disable()
gis.admin.credits.allocate(username, credits=None)
gis.admin.credits.deallocate(username)
gis.admin.license.all()
gis.admin.license.get(name)
```

### Servers

```python
gis.admin.servers.list()
gis.admin.servers.validate()
server.services.list(folder=None, refresh=True)
server.services.create_folder(folder_name, description='')
server.services.exists(folder_name, name=None, service_type=None)
server.services.publish_sd(sd_file, folder=None, service_config=None)
service.start()
service.stop()
service.delete()
service.rename(new_name)
datastore.validate()
datastore.update(item)
datastore.delete()
```

### Collaborations

```python
gis.admin.collaborations.create(name, description, workspace_name, workspace_description,
                                portal_group_id, host_contact_first_name,
                                host_contact_last_name, host_contact_email_address,
                                access_mode='sendAndReceive')
gis.admin.collaborations.list()
gis.admin.collaborations.accept_invitation(first_name, last_name, email,
                                           invitation_file=None, invitation_JSON=None,
                                           webauth_username=None, webauth_password=None,
                                           webauth_cert_file=None,
                                           webauth_cert_password=None)
collab.invite_participant(config_json, expiration=24, guest_portal_url=None,
                          guest_gis=None, save_path=None)
collab.import_invitation_response(response_file, webauth_username=None,
                                  webauth_password=None, webauth_cert_file=None,
                                  webauth_cert_password=None)
collab.pause_schedule(workspace_id)
collab.resume_schedule(workspace_id)
collab.sync(workspace_id, run_async=False)
```

## Practical interpretation notes

- `GIS`, `ContentManager`, `UserManager`, and `GroupManager` are the primary surfaces for this sub-skill.
- `Item.resources` is important for app-style or configuration-heavy items.
- `clone_items` is the safest first-choice cloning helper when supported item types are involved.
- `offline.import_content(..., failure_rollback=True)` is the safest choice for package-based migration when partial import would be harmful.
- Version- or entitlement-sensitive modules that were absent in this inspection environment should not be assumed available in later runs.
