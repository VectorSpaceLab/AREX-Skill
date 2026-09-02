#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

REQUIRED = ['schema_version','paper_id','experiment','is_proxy','sample_count','metrics','paper_target','commands','mechanism_checks']

def validate_result(result):
    errors=[f'missing {k}' for k in REQUIRED if k not in result]
    if not isinstance(result.get('metrics'), dict) or not any(isinstance(v,(int,float)) for v in result.get('metrics',{}).values()):
        errors.append('metrics must contain a numeric value')
    if result.get('is_proxy') and not result.get('mechanism_checks'):
        errors.append('proxy result needs mechanism checks')
    return {'ok': not errors, 'errors': errors}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result_json'); ap.add_argument('--output',required=True); args=ap.parse_args()
    result=json.loads(Path(args.result_json).read_text())
    Path(args.output).write_text(json.dumps(validate_result(result),indent=2)+'\n')
if __name__=='__main__': main()
