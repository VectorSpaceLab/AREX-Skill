# Alpamayo R1 troubleshooting

Use this file for cross-cutting package issues that affect the whole repository skill.
Workflow-specific inference failures live in `sub-skills/inference/references/troubleshooting.md`.

## Install or import fails

**Symptom:** `ImportError`, editable install failure, or missing distribution metadata.

**Likely causes:**

- Python is not 3.12.
- The editable install was not performed against the package checkout.
- A required runtime dependency is missing or incompatible.

**Fix:**

1. Use a Python 3.12 environment.
2. Install the package dependencies and the editable project install.
3. Verify with a minimal isolated import:

```bash
python -I -c "import alpamayo_r1, torch; print(torch.cuda.is_available())"
```

## CUDA backend is unavailable

**Symptom:** `torch.cuda.is_available()` is false, or the model cannot move to CUDA.

**Likely causes:**

- The runtime is using CPU-only torch.
- The host lacks a visible NVIDIA GPU.
- The driver or container passthrough is broken.

**Fix:**

- Confirm the host sees an NVIDIA GPU.
- Use the CUDA wheel path for torch 2.8.0.
- Re-run the backend smoke from the inspection environment.

This repository is CUDA-first. A CPU import does not validate the primary workflow.

## flash-attn build problems

**Symptom:** flash-attn fails to install, or the editable install reports a CUDA extension/toolchain error.

**Likely causes:**

- `CUDA_HOME` is unset or points to the wrong toolkit.
- The CUDA compiler toolchain is missing.
- The local GPU / driver combination is incompatible with the attempted flash-attn build.

**Fix:**

- Ensure a CUDA compiler is installed.
- Set `CUDA_HOME` to the active CUDA toolkit prefix before rebuilding flash-attn.
- If flash-attn still cannot be made to work, use the SDPA fallback documented in the inference sub-skill.

## Hugging Face gating and credentials

**Symptom:** model or dataset download returns a gated-resource or authorization error.

**Likely causes:**

- The Alpamayo model weights are gated.
- The PhysicalAI-AV dataset clip is gated.
- No HF login/token is available in the runtime.

**Fix:**

- Authenticate to Hugging Face before running the workflow.
- Confirm access to both gated resources.
- Reuse a validated clip id once access is available.

## Shared runtime reminders

- There is no public CLI entry point in this repository.
- Use the bundled smoke script for the end-to-end workflow.
- Keep the sub-skill router and the repo provenance file in sync with future repository updates.
