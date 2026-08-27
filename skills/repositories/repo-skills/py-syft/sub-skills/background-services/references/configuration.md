# Configuration

`syft-bg` config includes DO email, SyftBox root, notification settings, and approval policy:

```yaml
do_email: you@example.com
syftbox_root: ~/SyftBox
notify:
  interval: 30
  monitor_jobs: true
  monitor_peers: true
approve:
  interval: 5
  jobs:
    enabled: true
    peers:
      alice@example.com:
        mode: strict
        scripts:
          - name: main.py
            hash: sha256:...
  peers:
    enabled: false
    approved_domains: []
```

Gmail and Drive tokens are separate. Use data-owner scopes when generating tokens for notification/approval services. Keep config and token files private; do not paste token contents into replies.
