#!/usr/bin/env python3
"""Check WOD Frame utility imports and key signatures."""
from __future__ import annotations
import argparse, importlib, inspect, json

def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect Waymo Open Dataset frame utility signatures.')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    targets = [
        ('frame_utils', 'waymo_open_dataset.utils.frame_utils', ['parse_range_image_and_camera_projection','convert_range_image_to_point_cloud','convert_frame_to_dict']),
        ('range_image_utils', 'waymo_open_dataset.utils.range_image_utils', ['extract_point_cloud_from_range_image']),
        ('box_utils', 'waymo_open_dataset.utils.box_utils', ['is_within_box_3d']),
    ]
    result = {}
    ok = True
    for label, modname, attrs in targets:
        try:
            mod = importlib.import_module(modname)
            result[label] = {a: str(inspect.signature(getattr(mod,a))) for a in attrs}
        except Exception as exc:
            ok = False; result[label] = {'error': f'{type(exc).__name__}: {exc}'}
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if ok else 1
if __name__ == '__main__': raise SystemExit(main())
