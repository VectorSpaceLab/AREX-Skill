#!/usr/bin/env python3
"""Inspect the effective Mage project layout without mutating anything."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml


def resolve_variables_dir(project_path: Path, metadata_variables_dir: str | None, data_dir: str) -> str:
    if metadata_variables_dir:
        variables_dir = os.path.expanduser(metadata_variables_dir)
    else:
        variables_dir = os.path.expanduser(data_dir)

    if variables_dir.startswith(('s3://', 'gs://')):
        return variables_dir

    if os.path.isabs(variables_dir) and variables_dir != str(project_path):
        return os.path.join(variables_dir, project_path.name)
    return os.path.abspath(os.path.join(str(project_path), variables_dir))


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect Mage project paths.')
    parser.add_argument('--project-path', default='.', help='Mage project path to inspect.')
    args = parser.parse_args()

    project_path = Path(args.project_path).expanduser().resolve()
    metadata_path = project_path / 'metadata.yaml'
    io_config_path = project_path / 'io_config.yaml'

    metadata = {}
    if metadata_path.exists():
        with metadata_path.open('r', encoding='utf-8') as handle:
            metadata = yaml.safe_load(handle) or {}

    data_dir = os.getenv('MAGE_DATA_DIR', '~/.mage_data')
    variables_dir = resolve_variables_dir(project_path, metadata.get('variables_dir'), data_dir)

    info = {
        'project_path': str(project_path),
        'metadata_exists': metadata_path.exists(),
        'io_config_exists': io_config_path.exists(),
        'repo_name': project_path.name,
        'repo_path': str(project_path),
        'metadata_variables_dir': metadata.get('variables_dir'),
        'variables_dir': variables_dir,
        'data_dir': data_dir,
        'cwd': os.getcwd(),
    }
    print(json.dumps(info, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
