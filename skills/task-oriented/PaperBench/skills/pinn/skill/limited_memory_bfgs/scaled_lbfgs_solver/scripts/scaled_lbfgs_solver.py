from __future__ import annotations
from math import sqrt
from typing import Callable, List, Sequence
from pathlib import Path
import sys
try:
    from two_loop_direction import lbfgs_direction, dot
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parents[2] / 'two_loop_direction' / 'scripts'))
    from two_loop_direction import lbfgs_direction, dot
try:
    from curvature_memory import update_memory
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parents[2] / 'curvature_memory' / 'scripts'))
    from curvature_memory import update_memory
Vector=List[float]
def norm(v: Sequence[float]) -> float: return sqrt(dot(v,v))
def add(x: Sequence[float], a: float, p: Sequence[float]) -> Vector: return [xi+a*pi for xi,pi in zip(x,p)]
def minimize(objective: Callable[[Sequence[float]], float], gradient: Callable[[Sequence[float]], Vector], x0: Sequence[float], memory_limit: int=5, max_iter: int=25, tolerance: float=1e-8):
    x=list(x0); memory=[]; trace=[]; f=objective(x); g=gradient(x)
    for it in range(max_iter):
        gnorm=norm(g)
        trace.append({"iteration": it, "objective": f, "gradient_norm": gnorm, "memory_length": len(memory)})
        if gnorm <= tolerance: break
        direction_info=lbfgs_direction(g, memory)
        p=direction_info["direction"]
        if dot(p,g) >= 0: p=[-gi for gi in g]
        step=1.0
        while step > 1e-10:
            trial=add(x, step, p); ft=objective(trial)
            if ft <= f + 1e-4 * step * dot(g,p): break
            step *= 0.5
        x_new=add(x, step, p); g_new=gradient(x_new); f_new=objective(x_new)
        memory=update_memory(memory, x, x_new, g, g_new, memory_limit)
        trace[-1].update({"step": step, "scaling": direction_info["scaling"], "descent_dot": direction_info["descent_dot"]})
        x,g,f=x_new,g_new,f_new
    return {"x_final": x, "objective_final": f, "gradient_norm_final": norm(g), "trace": trace, "memory_final_length": len(memory)}
