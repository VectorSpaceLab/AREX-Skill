#!/usr/bin/env python3
from __future__ import annotations
import argparse
import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a minimal syft-bg config YAML")
    parser.add_argument("--email", required=True)
    parser.add_argument("--syftbox-root", required=True)
    parser.add_argument("--notify-interval", type=int, default=30)
    parser.add_argument("--approve-interval", type=int, default=5)
    args = parser.parse_args()
    data = {
        "do_email": args.email,
        "syftbox_root": args.syftbox_root,
        "notify": {"interval": args.notify_interval, "monitor_jobs": True, "monitor_peers": True},
        "approve": {"interval": args.approve_interval, "jobs": {"enabled": False, "peers": {}}, "peers": {"enabled": False, "approved_domains": []}},
    }
    print(yaml.safe_dump(data, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
