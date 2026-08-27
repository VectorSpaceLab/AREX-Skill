# Auth/sync API reference

| API | Verified shape | Use |
| --- | --- | --- |
| `syft_client.login_do` | `login_do(email=None, sync=True, load_peers=True, token_path=None, skip_peer_on_patch_version_diff=None)` | Data Owner login. |
| `syft_client.login_ds` | same shape | Data Scientist login. |
| `syft_rds.login_do` | `login_do(email=None, token_path=None, *, sync=True, load_peers=True, skip_peer_on_patch_version_diff=None)` | RDS DO login. |
| `syft_rds.login_ds` | same shape | RDS DS login. |
| `credentials_to_token` | `credentials_to_token(credentials_path, output_path=None, store=False, do_scopes=False, force_browserless=False)` | Create token JSON. |
| `client.add_peer` | `add_peer(peer_email, force=False, verbose=True, sync=True)` | Request peer link. |
| `client.load_peers` | `load_peers(force_download=False)` | Refresh peer state. |
| `client.approve_peer_request` | `approve_peer_request(email_or_peer, verbose=True, peer_must_exist=True)` | DO approval. |
| `client.sync` | `sync(auto_checkpoint=True, checkpoint_threshold=50)` | Synchronize local/remote state. |
| `client.delete_syftbox` | destructive cleanup | Ask first. |
