# syft-bg CLI reference

Safe discovery:

```bash
syft-bg --help
syft-bg status
syft-bg setup-status
```

Common commands:

```bash
syft-bg init -e you@example.com -r ~/SyftBox -t token_do.json
syft-bg ensure-running notify approve
syft-bg start notify
syft-bg stop approve
syft-bg restart notify
syft-bg logs notify
syft-bg tui
```

Auto-approval commands:

```bash
syft-bg auto-approve main.py -p alice@example.com
syft-bg list-auto-approvals
syft-bg remove-auto-approval utils.py -n my-analysis
syft-bg remove-peer alice@example.com
```

`install` and `uninstall` mutate systemd user services; ask before running them.
