#!/usr/bin/env python3
"""Inspect the dbt project layout inside a Mage project without running dbt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect Mage dbt project layout.')
    parser.add_argument('--project-path', default='.', help='Mage project path.')
    args = parser.parse_args()

    project_path = Path(args.project_path).expanduser().resolve()
    dbt_root = project_path / 'dbt'
    info = {'project_path': str(project_path), 'dbt_root_exists': dbt_root.exists(), 'dbt_projects': []}

    if dbt_root.exists():
        for child in sorted(dbt_root.iterdir()):
            if not child.is_dir():
                continue
            info['dbt_projects'].append({'path': str(child), 'dbt_project_yml_exists': (child / 'dbt_project.yml').exists(), 'profiles_yml_exists': (child / 'profiles.yml').exists(), 'profiles_yaml_exists': (child / 'profiles.yaml').exists(), 'model_count': len(list((child / 'models').rglob('*.sql'))) if (child / 'models').exists() else 0})

    print(json.dumps(info, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
