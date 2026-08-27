#!/usr/bin/env python3
"""Check DeepFace database backend configuration without connecting by default."""
from __future__ import annotations
import argparse, importlib.util, json, os
BACKENDS={"postgres":{"vector":False,"env":"DEEPFACE_POSTGRES_URI","modules":["psycopg"]},"mongo":{"vector":False,"env":"DEEPFACE_MONGO_URI","modules":["pymongo"]},"weaviate":{"vector":True,"env":"DEEPFACE_WEAVIATE_URI","modules":["weaviate"]},"neo4j":{"vector":True,"env":"DEEPFACE_NEO4J_URI","modules":["neo4j"]},"pgvector":{"vector":True,"env":"DEEPFACE_POSTGRES_URI","modules":["psycopg","pgvector"]},"pinecone":{"vector":True,"env":"DEEPFACE_PINECONE_API_KEY","modules":["pinecone"]},"milvus":{"vector":True,"env":"DEEPFACE_MILVUS_URI","modules":["pymilvus"]}}

def main()->int:
    ap=argparse.ArgumentParser(description='Validate DeepFace database backend config without connecting.')
    ap.add_argument('--database-type', default=os.getenv('DEEPFACE_DATABASE_TYPE','postgres').lower())
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args(); backend=BACKENDS.get(args.database_type); issues=[]
    if backend is None:
        issues.append(f'Unsupported database_type: {args.database_type}'); report={'ok':False,'issues':issues,'known_backends':sorted(BACKENDS)}
    else:
        env_var=backend['env']; env_present=bool(os.getenv('DEEPFACE_CONNECTION_DETAILS') or os.getenv(env_var)); imports={m: importlib.util.find_spec(m) is not None for m in backend['modules']}
        if not env_present: issues.append(f'Missing DEEPFACE_CONNECTION_DETAILS or {env_var}')
        for mod, ok in imports.items():
            if not ok: issues.append(f'Missing optional Python module: {mod}')
        report={'ok':not issues,'database_type':args.database_type,'is_vector_db':backend['vector'],'connection_env':env_var,'connection_env_present':env_present,'imports':imports,'issues':issues}
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else ('OK' if report['ok'] else 'ISSUES\n- ' + '\n- '.join(issues)))
    return 0 if report['ok'] else 2
if __name__=='__main__': raise SystemExit(main())
