#!/usr/bin/env python3
"""Inspect WOD V2 component tags and run tiny component/dataframe checks."""
import argparse, dataclasses, json

def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Waymo Open Dataset V2 component helpers.")
    parser.add_argument('--json', action='store_true', help='Emit JSON.')
    args = parser.parse_args()
    result = {}
    try:
        import pandas as pd
        import pyarrow as pa
        from waymo_open_dataset import v2
        from waymo_open_dataset.v2 import component
        @dataclasses.dataclass
        class TinyKey(component.Key):
            segment_context_name: str = component.create_column(arrow_type=pa.string())
        @dataclasses.dataclass
        class TinyComponent(component.Component):
            key: TinyKey
            score: float = component.create_column(arrow_type=pa.float32())
        row = TinyComponent(key=TinyKey('ctx'), score=0.5)
        flat = row.to_flatten_dict()
        restored = TinyComponent.from_dict(flat)
        left = pd.DataFrame({'key.segment_context_name': ['ctx'], 'left': [1]})
        right = pd.DataFrame({'key.segment_context_name': ['ctx'], 'right': [2]})
        merged = v2.merge(left, right)
        result = {'ok': True, 'tags': list(v2.ALL_TAGS), 'flat_keys': list(flat.keys()), 'schema': str(TinyComponent.schema()), 'restored_score': restored.score, 'merged_columns': list(merged.columns)}
    except Exception as exc:
        result = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)
    return 0 if result.get('ok') else 1
if __name__ == '__main__': raise SystemExit(main())
