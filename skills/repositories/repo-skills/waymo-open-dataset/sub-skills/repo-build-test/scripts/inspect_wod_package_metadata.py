#!/usr/bin/env python3
"""Print distilled Waymo Open Dataset package metadata."""
from __future__ import annotations
import argparse, json
from importlib import metadata

DISTILLED = {
    'distribution': 'waymo-open-dataset-tf-2-12-0',
    'version_from_bazel_wheel_rule': '1.6.7',
    'import_name': 'waymo_open_dataset',
    'tensorflow_line': '2.13',
    'python_note': 'Use Python 3.10 for the verified 1.6.7 package line when jaxlib==0.4.13 resolution matters.',
    'wheel_targets': ['//waymo_open_dataset/pip_pkg_scripts:wheel', '//waymo_open_dataset/pip_pkg_scripts:wheel_manylinux'],
    'requirements_update_target': '//waymo_open_dataset:requirements.update',
}

def main() -> int:
    parser=argparse.ArgumentParser(description='Inspect distilled WOD package metadata.')
    parser.add_argument('--json', action='store_true')
    args=parser.parse_args()
    result=dict(DISTILLED)
    try: result['installed_version']=metadata.version(DISTILLED['distribution'])
    except metadata.PackageNotFoundError: result['installed_version']=None
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0
if __name__=='__main__': raise SystemExit(main())
