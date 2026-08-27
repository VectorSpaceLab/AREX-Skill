#!/usr/bin/env python3
"""Safe DeepFace environment diagnostic.

Imports public package metadata and inventories without building models,
downloading weights, connecting to databases, opening cameras, or calling the
REST API.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from importlib.metadata import PackageNotFoundError, version

def dist_version(name: str):
    try: return version(name)
    except PackageNotFoundError: return None

def main() -> int:
    ap = argparse.ArgumentParser(description="Check DeepFace importability and static inventories.")
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    report = {'python': sys.version.split()[0], 'distributions': {n: dist_version(n) for n in ['deepface','tensorflow','keras','tf-keras','opencv-python','retina-face','mtcnn']}, 'imports': {}, 'inventories': {}, 'warnings': []}
    try:
        import deepface
        report['imports']['deepface'] = {'ok': True, 'version': getattr(deepface, '__version__', None)}
    except Exception as exc:
        report['imports']['deepface'] = {'ok': False, 'error': repr(exc)}
        print(json.dumps(report, indent=2) if args.json else f'DeepFace import failed: {exc!r}')
        return 1
    try:
        from deepface import DeepFace
        report['imports']['deepface.DeepFace'] = {'ok': True}
        report['public_functions'] = [n for n in ['build_model','verify','analyze','find','represent','stream','extract_faces','register','search','build_index','detectFace'] if hasattr(DeepFace, n)]
    except Exception as exc:
        report['imports']['deepface.DeepFace'] = {'ok': False, 'error': repr(exc)}
        report['warnings'].append('DeepFace facade import failed; TensorFlow/Keras compatibility or optional detector imports may need attention.')
    try:
        from deepface.modules.modeling import AVAILABLE_MODELS
        report['inventories']['models'] = {task: sorted(models.keys()) for task, models in AVAILABLE_MODELS.items()}
    except Exception as exc: report['inventories']['models_error'] = repr(exc)
    try:
        from deepface.modules.database.inventory import database_inventory
        report['inventories']['databases'] = {k: {'is_vector_db': v['is_vector_db'], 'env_var': v['connection_string']} for k,v in database_inventory.items()}
    except Exception as exc: report['inventories']['databases_error'] = repr(exc)
    for mod in ['tf_keras','psycopg','pgvector','pymongo','weaviate','neo4j','pinecone','pymilvus','ultralytics','dlib','mediapipe','insightface','onnxruntime']:
        report['imports'][mod] = {'ok': importlib.util.find_spec(mod) is not None}
    if args.json: print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print('DeepFace environment diagnostic')
        for k,v in report['distributions'].items(): print(f'  {k}: {v or "not installed"}')
        for k,v in report['imports'].items(): print(f'  {k}: {"ok" if v["ok"] else v.get("error", "missing")}')
    return 0 if report['imports'].get('deepface',{}).get('ok') else 1
if __name__ == '__main__': raise SystemExit(main())
