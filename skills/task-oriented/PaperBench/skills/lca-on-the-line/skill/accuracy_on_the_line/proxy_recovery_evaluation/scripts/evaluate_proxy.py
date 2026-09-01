#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
REQUIRED_CHECKS=['paired_records_validated','line_fit_executed','correlation_computed','residuals_inspected','proxy_declared','source_boundary_respected']

def evaluate_proxy(calibration, checks, threshold):
    r=float(calibration.get('pearson_r'))
    missing=[name for name in REQUIRED_CHECKS if checks.get(name) is not True]
    metric_gap=r-float(threshold)
    accepted=(not missing) and metric_gap >= 0
    reasons=[]
    if missing: reasons.append('missing mechanism checks: '+', '.join(missing))
    if metric_gap < 0: reasons.append(f'pearson_r below threshold by {-metric_gap:.6f}')
    if not reasons: reasons.append('declared proxy exercises paired accuracy line mechanism')
    return {'accepted_proxy':accepted,'mechanism_ok':not missing,'pearson_r':r,'threshold':float(threshold),'metric_gap':metric_gap,'missing_checks':missing,'reasons':reasons}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--calibration', required=True); ap.add_argument('--checks', required=True); ap.add_argument('--threshold', type=float, required=True); ap.add_argument('--output', default='')
    args=ap.parse_args(); result=evaluate_proxy(json.loads(Path(args.calibration).read_text()), json.loads(Path(args.checks).read_text()), args.threshold)
    text=json.dumps(result, indent=2)
    if args.output: Path(args.output).write_text(text + chr(10))
    print(text)
if __name__ == '__main__': main()
