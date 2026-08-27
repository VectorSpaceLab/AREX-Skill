#!/usr/bin/env python3
"""Safe API-surface check for Libra text generation."""
from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
REPO_ROOT = SCRIPT_DIR.parents[5]
for candidate in (ROOT / 'scripts', REPO_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from libra_compat import apply


def main() -> int:
    parser = argparse.ArgumentParser(description='Check the Libra generate_text path without forcing GPT-2 downloads by default.')
    parser.add_argument('--prefix', default='Once upon a time', help='Prefix to use in the suggested prefix-mode call.')
    parser.add_argument('--file-data', action='store_true', help='Suggest file-backed generation instead of prefix mode.')
    parser.add_argument('--run', action='store_true', help='Actually call generate_text. This may download GPT-2 weights.')
    parser.add_argument('--allow-download', action='store_true', help='Acknowledge that model downloads/cache misses are allowed for --run.')
    parser.add_argument('--json', action='store_true', help='Emit JSON report.')
    args = parser.parse_args()

    apply()
    from libra import client
    apply()

    signature = str(inspect.signature(client.generate_text))
    report = {
        'method': 'client.generate_text',
        'signature': signature,
        'safe_default': 'dry-run only; no GPT-2 download is attempted',
        'recommended_call': (
            "c.generate_text(max_length=64, return_sequences=1)"
            if args.file_data else
            f"c.generate_text(file_data=False, prefix={args.prefix!r}, max_length=64, return_sequences=1)"
        ),
    }

    if args.run and not args.allow_download:
        report['blocked'] = 'Refusing --run without --allow-download because GPT-2 weights may be fetched.'
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            for key, value in report.items():
                print(f'{key}: {value}')
        return 2

    if args.run:
        client.required_installations = lambda self: None
        with tempfile.TemporaryDirectory(prefix='libra-text-generation-') as tmpdir:
            text_path = Path(tmpdir) / 'seed.txt'
            text_path.write_text(args.prefix + '\n')
            c = client(str(text_path))
            if args.file_data:
                c.generate_text(max_length=64, return_sequences=1)
            else:
                c.generate_text(file_data=False, prefix=args.prefix, max_length=64, return_sequences=1)
            report['ran'] = True
            report['model_key'] = 'text_generation'
            report['generated_text_length'] = len(c.models['text_generation']['generated_text'])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key, value in report.items():
            print(f'{key}: {value}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
