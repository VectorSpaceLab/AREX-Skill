# Web UI and Deployment Troubleshooting

## Blank task rejected

**Symptom:** status says the question is invalid. **Cause:** `validate_input`
rejects empty/whitespace text. **Recovery:** supply a concrete task including
required files/URLs and output expectation; do not encode keys in the task.

## Module cannot be imported or lacks `construct_society`

**Symptom:** UI reports unsupported module, import error, or incompatible
interface. **Cause:** selected name is absent from `MODULE_DESCRIPTIONS`, is
listed but no matching `examples.<name>` file exists, import dependencies fail,
or the module has no `construct_society`. **Recovery:** run
`check_web_ui_config.py`, choose a present provider example, and solve provider
errors in [workforce-workflows](../../workforce-workflows/SKILL.md). Do not
create an empty placeholder module just to bypass the check.

## UI cannot find `utils`

**Symptom:** importing/running webapp produces `ModuleNotFoundError: utils`.
**Cause:** source is script-oriented and expects its own `owl` directory on the
script path. **Recovery:** launch using the project/script layout that matches
the package source, or package a deployment wrapper with an explicit controlled
entry point. Avoid broad `PYTHONPATH` changes that mask unrelated packages.

## Credential file behavior is unsafe or fails to save

**Symptom:** a save/add/delete error, wrong key takes precedence, or secret is
shown in a log. **Recovery:** stop UI-based editing, use a protected env file or
host secret manager, check file ownership/writability, redact logs, and restart
with a minimal selected provider configuration. UI env callbacks can mutate
both file and process environment.

## Gradio/port/display failure

**Symptom:** import error, address already in use, page inaccessible, or display
failure. **Recovery:** verify the declared Gradio dependency, select an unused
local port, bind only to the intended interface, and use Xvfb/headless browser
setup for display-dependent tasks. A UI server should not be exposed publicly
without access controls.

## Docker/Compose failure

**Symptom:** Docker daemon unavailable, Compose command missing, image pull/build
fails, mount denied, or service never becomes healthy. **Recovery:** run
`check_docker_runtime.sh`, correct host/daemon/Compose installation, validate
mount ownership and env file path, then review build/network permissions before
retrying. Do not run cache cleanup or volume pruning as a generic fix.

## Browser/Playwright failure

**Symptom:** browser executable missing, sandbox error, or X11/Xvfb issue.
**Recovery:** install required browser assets/system libraries in the selected
runtime, use the correct headless/display option, and test one approved browser
operation. Browser failure does not invalidate non-browser Workforce tasks.
