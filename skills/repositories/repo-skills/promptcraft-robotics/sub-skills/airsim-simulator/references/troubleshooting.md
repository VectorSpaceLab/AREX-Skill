# AirSim simulator troubleshooting

This page focuses on the sample-specific issues that tend to block use of the ChatGPT-AirSim workflow.

## API key problems

**Symptom**
- The sample initializes but cannot talk to the model provider.

**Likely cause**
- The config file still contains a placeholder key or the key is malformed.

**Recovery**
- Use `scripts/check-chatgpt-airsim-config.py` to confirm the config shape.
- Replace the placeholder with a valid key before trying the runtime.

## Import or dependency problems

**Symptom**
- `ModuleNotFoundError` for `openai`, `numpy`, or `airsim`.

**Likely cause**
- The environment does not match the inspected dependency stack.

**Recovery**
- Recreate or repair the Python environment with the repo's published dependency pins.
- Re-run the import smoke checks before trying the sample again.

## AirSim connection problems

**Symptom**
- The wrapper cannot confirm a connection or the simulator appears unreachable.

**Likely cause**
- The simulator is not running, not configured, or not accessible from the current machine.

**Recovery**
- Confirm the AirSim runtime is up before instantiating the wrapper.
- Check the simulator settings file and confirm the sample mode is multirotor/drone-oriented.

## Relative-path problems

**Symptom**
- Prompt or system prompt files are reported as missing.

**Likely cause**
- The sample was launched from a directory that does not match its expected relative paths.

**Recovery**
- Validate the file paths before launch.
- Prefer absolute paths in your own wrapper logic if you are adapting the sample.

## Unsafe execution problems

**Symptom**
- The assistant output contains code that should not be run unchanged.

**Likely cause**
- The sample executes fenced code blocks directly.

**Recovery**
- Treat the sample as a sandboxed demonstration.
- Manually review any generated code before executing it against a live simulator.

## Coordinate or object-name problems

**Symptom**
- The drone goes the wrong way or targets the wrong landmark.

**Likely cause**
- The user-facing prompt convention and the wrapper's internal movement conversion were mixed up.
- The prompt guessed between duplicated object names instead of asking for clarification.

**Recovery**
- Re-check the available helper functions and the object list.
- Ask a clarification question if the object type is duplicated.
- Recompute the target motion using the documented axis convention.
