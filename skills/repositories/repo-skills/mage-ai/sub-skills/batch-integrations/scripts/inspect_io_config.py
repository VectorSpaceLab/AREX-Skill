#!/usr/bin/env python3
"""Inspect an io_config.yaml file without printing secrets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect Mage io_config profiles.')
    parser.add_argument('--project-path', default='.', help='Mage project path.')
    parser.add_argument('--profile', default='default', help='Profile name to inspect.')
    args = parser.parse_args()

    project_path = Path(args.project_path).expanduser().resolve()
    io_config_path = project_path / 'io_config.yaml'

    if not io_config_path.exists():
        print(json.dumps({'project_path': str(project_path), 'io_config_exists': False}, indent=2, sort_keys=True))
        return 1

    raw = yaml.safe_load(io_config_path.read_text(encoding='utf-8')) or {}
    profile_data = raw.get(args.profile) or {}
    result = {
        'project_path': str(project_path),
        'io_config_exists': True,
        'profiles': sorted(raw.keys()),
        'selected_profile': args.profile,
        'selected_profile_exists': args.profile in raw,
        'selected_profile_keys': sorted(profile_data.keys()) if isinstance(profile_data, dict) else [],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
