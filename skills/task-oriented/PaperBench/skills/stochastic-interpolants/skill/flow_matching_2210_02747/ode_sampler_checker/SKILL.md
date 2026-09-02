---
name: ode_sampler_checker
description: Integrate simple Flow Matching vector fields and verify ODE trajectory, endpoint, and NFE evidence.
---
# ODE Sampler Checker
Use this skill for bounded CNF ODE sampling checks. Inputs are `x0`, velocity/callback, step count, and optional target; outputs are trajectory, final state, NFE, and endpoint error. Run `python tests/test_ode_sampler.py`. It validates mechanics, not FID.
