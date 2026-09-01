---
name: tsnpe_reduced_recovery_harness
description: Run a bounded mechanism-faithful TSNPE proxy recovery experiment.
---

# Tsnpe Reduced Recovery Harness

Use this skill when full TSNPE benchmark recovery is blocked by heavy package, simulator, or data requirements and soft mode permits a declared proxy. The harness must call the generated HPR, training, and diagnostic scripts, produce executable evidence, and label the result as reduced/proxy.

Inputs: attempt directory, module plan, runtime handoff, and generated skill root. Outputs: recovery result and logs under the attempt recovery directory. Validation: run the harness followed by the Distiller recovery validator. For reduced Gaussian recovery, accept the proxy only when loss decreases, ground-truth support inclusion is at least 0.5, absolute mean error is finite and below 1.0, and all mechanism checks remain true.

