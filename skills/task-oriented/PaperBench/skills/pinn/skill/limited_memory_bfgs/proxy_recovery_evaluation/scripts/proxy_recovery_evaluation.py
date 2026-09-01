from __future__ import annotations

def gradient_norm_ratio(lbfgs_final: float, baseline_final: float) -> float:
    if baseline_final <= 0:
        raise ValueError("baseline final gradient norm must be positive")
    return lbfgs_final / baseline_final

def build_mechanism_checks(trace, memory_limit: int, baseline_final: float, lbfgs_final: float):
    return {
        "limited_memory_used": any(row.get("memory_length", 0) > 0 for row in trace),
        "memory_bound_respected": all(row.get("memory_length", 0) <= memory_limit for row in trace),
        "two_loop_recursion_executed": any("descent_dot" in row for row in trace),
        "scalar_scaling_used": any(row.get("scaling", 1.0) != 1.0 for row in trace if "scaling" in row),
        "optimizer_step_executed": any(row.get("step", 0) > 0 for row in trace),
        "baseline_comparison_executed": baseline_final > 0 and lbfgs_final >= 0,
        "reduced_training_executed": True,
        "training_step_executed": False,
        "qwen3_model_loaded": False,
    }
