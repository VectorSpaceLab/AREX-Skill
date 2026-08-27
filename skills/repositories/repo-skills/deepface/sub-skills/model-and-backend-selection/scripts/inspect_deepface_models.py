#!/usr/bin/env python3
"""Inspect installed DeepFace static model/backend inventories."""
from __future__ import annotations
import argparse, json
from importlib.metadata import PackageNotFoundError, version

def v(name:str):
    try: return version(name)
    except PackageNotFoundError: return None

def main()->int:
    ap=argparse.ArgumentParser(description='Print DeepFace model, detector, threshold, and database inventories.')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--build', nargs=2, metavar=('TASK','MODEL'), help='Optionally build one model; may download weights.')
    args=ap.parse_args()
    from deepface.modules.modeling import AVAILABLE_MODELS, build_model
    from deepface.modules.database.inventory import database_inventory
    from deepface.config.threshold import thresholds
    report={'versions':{name:v(name) for name in ['deepface','tensorflow','keras','tf-keras']},'models':{task:sorted(models.keys()) for task,models in AVAILABLE_MODELS.items()},'databases':{key:{'is_vector_db':spec['is_vector_db'],'env_var':spec['connection_string']} for key,spec in database_inventory.items()},'threshold_models':sorted(thresholds)}
    if args.build:
        task, model_name = args.build; obj = build_model(task=task, model_name=model_name); report['build']={'task':task,'model_name':model_name,'class':obj.__class__.__name__}
    if args.json: print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print('Versions:')
        for k,val in report['versions'].items(): print(f'  {k}: {val or "not installed"}')
        print('Models:')
        for task,names in report['models'].items(): print(f'  {task}: {", ".join(names)}')
        print('Databases:')
        for key,spec in report['databases'].items(): print(f"  {key}: vector={spec['is_vector_db']} env={spec['env_var']}")
    return 0
if __name__=='__main__': raise SystemExit(main())
