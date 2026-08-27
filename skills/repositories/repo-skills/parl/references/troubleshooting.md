# PARL Cross-cutting Troubleshooting

## Import and installation

### `import parl` succeeds but `parl.Model` is missing

Likely cause: no supported deep learning framework was importable when PARL loaded, or the process intentionally skipped core imports for xparl-only use.

Recovery:

1. Decide the target backend (`torch`, `paddle`, or legacy `fluid`).
2. Install that backend in the target environment.
3. Start a fresh Python process with `PARL_BACKEND=<backend>` set before `import parl`.
4. Run `python scripts/check_parl_install.py --backend <backend>` from this skill to confirm aliases.

### The wrong backend is selected

PARL chooses Paddle 2.x first, then legacy Fluid, then Torch when `PARL_BACKEND` is unset. If both Paddle and Torch are installed, set `PARL_BACKEND` before importing PARL.

```bash
PARL_BACKEND=torch python scripts/check_parl_install.py --backend torch
```

Do not change `PARL_BACKEND` after `import parl`; start a new process.

### Source checkout installs but imports only from the checkout directory

Some legacy editable-install paths can fail outside the checkout with modern packaging tools. Use one of these public remedies:

- Prefer `pip install parl` for normal users who do not need local source edits.
- For a local source checkout, use a modern compatible Python and verify import from a neutral directory after installation.
- If editable mode behaves unexpectedly, reinstall with a compatibility editable mode or use a non-editable wheel/source install, then rerun the root checker.

## Dependency and backend compatibility

### Torch/NumPy compatibility warnings

Older Torch wheels may warn or fail with NumPy 2.x. Either use a Torch release that supports NumPy 2.x or pin NumPy to a 1.x release that the backend and PARL examples tolerate.

### Paddle and Fluid mismatch

- Paddle 2.x backs `parl.core.paddle` and modern Paddle examples.
- Legacy Fluid expects old Paddle packages and should not be mixed with a modern Paddle-only environment.
- If a task specifically names Fluid examples, treat it as a legacy environment request and isolate it from modern Paddle/Torch installs.

### Optional framework packages are absent

PARL's base package can still support xparl remote execution and some utilities, but algorithm/model code needs a framework backend. Route to:

- `sub-skills/core-framework/SKILL.md` for backend alias checks.
- `sub-skills/algorithm-recipes/SKILL.md` for algorithm-specific model-method requirements.
- `sub-skills/environment-utils/SKILL.md` for wrappers and utilities that may need Gym/MuJoCo/Atari/PettingZoo extras.

## xparl cluster and security issues

- `xparl start` starts processes and binds ports. Use help/status checks before starting new services on shared machines.
- Do not expose xparl ports to untrusted networks. Remote execution relies on serialized Python behavior and is only appropriate for trusted machines and code.
- If ports or stale workers are suspected, inspect status and process ownership before using `xparl stop` or killing processes.
- See `sub-skills/xparl-distributed/SKILL.md` for safe cluster lifecycle guidance.

## Training and examples

- Most examples perform real environment interaction, checkpoint writes, and potentially long training. Prefer algorithm catalog and helper checks first.
- MuJoCo, Atari, SMAC, OpenSim, D4RL, and challenge examples require additional packages, data, licenses, or services. Do not treat a base PARL install as sufficient for those examples.
- TIPC scripts may install packages, download data, control xparl processes, and mutate the host. Treat them as reference-only unless the user authorizes those side effects.

## Optional specialized workflows

- Waymax-RL has no CPU substitute for its all-GPU training claim. Validate its config first, then install JAX CUDA/Waymax/data requirements in a dedicated environment.
- EvoKit is a native C++ toolkit. Run the prerequisite checker before any build; do not execute upstream build scripts in a shared checkout unless downloads, build-dir deletion, and demo execution are acceptable.
