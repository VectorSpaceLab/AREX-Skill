# Authentication

Typical local/Jupyter login:

```python
import syft_client as sc
owner = sc.login_do(email="owner@example.com", token_path="token_owner.json")
scientist = sc.login_ds(email="scientist@example.com", token_path="token_ds.json")
```

Equivalent RDS login returns a `SyftRDSClient` with datasets/jobs:

```python
from syft_rds import login_do, login_ds
owner = login_do(email="owner@example.com", token_path="token_owner.json")
scientist = login_ds(email="scientist@example.com", token_path="token_ds.json")
```

`credentials_to_token(credentials_path, output_path=None, store=False, do_scopes=False, force_browserless=False)` converts a desktop-client OAuth credentials JSON into an authorized token. Set `do_scopes=True` only for data-owner background services that need Gmail/Pub/Sub.

Never print OAuth secrets. Prefer shape/email validation first:

```bash
python scripts/validate_token_file.py --token-path token_owner.json --expect-email owner@example.com
```

Add `--live-drive-check` only after the user authorizes a network/token-refreshing check.
