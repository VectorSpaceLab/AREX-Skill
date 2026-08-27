#!/usr/bin/env python3
"""Check or download NLTK corpora needed by legacy Libra NLP workflows."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[5]
for candidate in (SCRIPT_DIR, REPO_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

CORPORA = {
    'punkt': ['tokenizers/punkt'],
    'punkt_tab': ['tokenizers/punkt_tab/english'],
    'averaged_perceptron_tagger': ['taggers/averaged_perceptron_tagger'],
    'averaged_perceptron_tagger_eng': ['taggers/averaged_perceptron_tagger_eng'],
    'stopwords': ['corpora/stopwords'],
    'wordnet': ['corpora/wordnet'],
    'omw-1.4': ['corpora/omw-1.4'],
}


def find_status():
    import nltk

    report = {}
    for corpus, resources in CORPORA.items():
        present = False
        found_at = None
        for resource in resources:
            try:
                found_at = str(nltk.data.find(resource))
                present = True
                break
            except LookupError:
                continue
        report[corpus] = {'present': present, 'path': found_at, 'resources': resources}
    return report


def print_text(report):
    for corpus, item in report.items():
        status = 'present' if item['present'] else 'missing'
        suffix = f" ({item['path']})" if item['path'] else ''
        print(f'{corpus}: {status}{suffix}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Check/download NLTK corpora for Libra NLP workflows.')
    parser.add_argument('--check', action='store_true', help='Check corpus availability. This is the default.')
    parser.add_argument('--download', action='store_true', help='Download missing corpora. Requires approved network access.')
    parser.add_argument('--require', action='store_true', help='Exit nonzero if any corpus is missing after checks/downloads.')
    parser.add_argument('--json', action='store_true', help='Emit JSON report.')
    args = parser.parse_args()

    import nltk

    report = find_status()
    missing = [name for name, item in report.items() if not item['present']]

    if args.download and missing:
        for name in missing:
            try:
                nltk.download(name)
            except Exception as exc:  # pragma: no cover - environment/network dependent
                print(f'download failed for {name}: {exc}', file=sys.stderr)
        report = find_status()
        missing = [name for name, item in report.items() if not item['present']]

    if args.json:
        print(json.dumps({'corpora': report, 'missing': missing}, indent=2, sort_keys=True))
    else:
        print_text(report)
        if missing:
            print('missing:', ', '.join(missing))
            print('If a proxied download is blocked, pre-stage corpora or allow the proxy only when trusted.')
        else:
            print('all configured corpora are present')

    if args.require and missing:
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
