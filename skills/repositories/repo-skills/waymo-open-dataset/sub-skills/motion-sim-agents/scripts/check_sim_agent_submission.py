#!/usr/bin/env python3
"""Print WOD sim-agent challenge type and config basics."""
from __future__ import annotations
import argparse, dataclasses, json

def main() -> int:
    parser=argparse.ArgumentParser(description='Check WOD sim-agent submission helper imports.')
    parser.add_argument('--json', action='store_true')
    args=parser.parse_args()
    try:
        from waymo_open_dataset.utils.sim_agents import submission_specs
        data={}
        for challenge in submission_specs.ChallengeType:
            cfg=submission_specs.get_submission_config(challenge)
            data[challenge.value]=dataclasses.asdict(cfg)
        result={'ok': True, 'challenge_types': [c.value for c in submission_specs.ChallengeType], 'configs': data}
    except Exception as exc:
        result={'ok': False, 'error': f'{type(exc).__name__}: {exc}'}
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if result.get('ok') else 1
if __name__=='__main__': raise SystemExit(main())
