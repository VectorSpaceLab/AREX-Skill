#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate a generated Upsonic project config.')
    parser.add_argument('config', type=Path)
    args = parser.parse_args()

    data = json.loads(args.config.read_text(encoding='utf-8'))
    errors: list[str] = []
    if 'agent_name' not in data:
        errors.append('missing agent_name')
    entrypoints = data.get('entrypoints', {})
    if 'api_file' not in entrypoints:
        errors.append('missing entrypoints.api_file')
    if 'input_schema' not in data:
        errors.append('missing input_schema')
    if 'output_schema' not in data:
        errors.append('missing output_schema')

    if errors:
        for error in errors:
            print(error)
        return 1

    print(f'{args.config}: valid')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
