from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path

def run_command(cmd, cwd):
    t=time.time(); p=subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=120)
    return {'command':' '.join(cmd),'returncode':p.returncode,'elapsed_seconds':round(time.time()-t,3),'stdout_tail':p.stdout[-2000:],'stderr_tail':p.stderr[-2000:]}

def validate_result(result, max_gradient_error=1e-5, min_improvement=1e-6):
    checks=result.get('mechanism_checks',{})
    metric=result.get('metrics',{}).get('max_gradient_error', 1.0)
    return bool(metric <= max_gradient_error and result.get('metrics',{}).get('objective_improvement',0) > min_improvement and checks.get('policy_gradient_theorem_checked') and checks.get('compatible_critic_orthogonality_checked') and checks.get('optimizer_step_executed'))
