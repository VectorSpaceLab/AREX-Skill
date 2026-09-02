#!/usr/bin/env python3
import argparse, json, subprocess, sys, time
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--attempt-dir', required=True); ap.add_argument('--skills-root', required=True)
    ns=ap.parse_args(); attempt=Path(ns.attempt_dir); skills=Path(ns.skills_root); logs=attempt/'recovery'/'logs'; logs.mkdir(parents=True, exist_ok=True)
    train_script=skills/'lora_training_step'/'scripts'/'reduced_training.py'
    trace=logs/'training_trace.json'
    t0=time.time(); proc=subprocess.run([sys.executable,str(train_script),'--output',str(trace),'--steps','12','--lr','0.1'], text=True, capture_output=True, timeout=30)
    command={'command':' '.join([sys.executable,str(train_script),'--output',str(trace),'--steps','12','--lr','0.1']),'returncode':proc.returncode,'elapsed_seconds':round(time.time()-t0,3),'stdout_tail':proc.stdout[-2000:],'stderr_tail':proc.stderr[-2000:]}
    data=json.loads(trace.read_text())
    result={'trace':str(trace),'ok':proc.returncode==0 and data['loss_after']<data['loss_before'] and data['base_weight_unchanged'] and data['merge_max_abs_diff']<1e-12,'loss_reduction_ratio':(data['loss_before']-data['loss_after'])/data['loss_before'],'command':command}
    print(json.dumps(result, indent=2))
    return 0 if result['ok'] else 2
if __name__ == '__main__': raise SystemExit(main())
