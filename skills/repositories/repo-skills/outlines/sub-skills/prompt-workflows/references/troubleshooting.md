# Troubleshooting Prompt Workflows

## Missing Jinja variables

**Symptom:** rendering raises `jinja2.exceptions.UndefinedError` or the prompt has an unresolved placeholder.

**Cause:** Outlines templates use `StrictUndefined`, so every variable referenced in the template must be supplied.

**Fix:**

- Render with the full mapping before calling a model.
- Add a tiny render test for every new template.
- Prefer explicit variable names over large implicit contexts.

```python
from outlines import Template

template = Template.from_string("Hello {{ name }}")
assert template(name="Ada") == "Hello Ada"
```

## Template loader and include boundaries

**Symptom:** `Template.from_file(...)` fails to resolve `{% include %}` or `{% extends %}` files outside the template directory.

**Cause:** file-backed templates are rooted at the file's parent directory. Includes and inheritance are intentionally bounded there.

**Fix:**

- Bundle dependent templates under one directory tree.
- Move shared fragments beside the root template or into subdirectories.
- Do not rely on repository-relative paths unless you explicitly control them in the bundled skill.

**Never do this:** point runtime documentation or scripts at the source checkout as a dependency.

## Path handling

**Symptom:** a file path works from one working directory but not another.

**Cause:** the template path was assumed to be relative to the current shell instead of the script or bundled asset boundary.

**Fix:**

- Resolve user-provided paths deliberately.
- Keep bundled templates and scripts in the skill tree.
- Avoid hidden assumptions about the caller's working directory.

## Chat role/content shape

**Symptom:** a provider adapter rejects a `Chat` object, or chat rendering fails after the prompt looked correct.

**Cause:** `Chat` itself only stores message dictionaries. The selected model adapter may require a stricter shape than `Chat` permits.

**Fix:**

- Ensure every message has `role` and `content`.
- Keep role values limited to `system`, `user`, and `assistant` unless the adapter explicitly says otherwise.
- Make sure multimodal content is in the form the adapter expects: string, text-plus-asset list, or an explicit typed structure.
- If the model is not chat-capable, route to the correct sibling skill before building the workflow.

## Image format and base64 failures

**Symptom:** `Image(...)` raises `TypeError: Could not read the format of the image passed to the model.`

**Cause:** the PIL image object had no usable `format` attribute.

**Fix:**

- Load the image from a file or buffer that preserves `format`.
- If you create an image in memory, set `image.format` before wrapping it or save/reopen it with PIL.
- Do not pass raw bytes directly to `Image`; it expects a PIL image.

```python
from PIL import Image as PILImage
from outlines.inputs import Image

img = PILImage.new("RGB", (8, 8), color="white")
img.format = "PNG"
asset = Image(img)
```

## Provider asset support

**Symptom:** a prompt with `Image`, `Audio`, or `Video` is rejected by the model/provider.

**Cause:** the asset wrapper is syntactically valid, but the selected backend does not support that modality or expects a different content shape.

**Fix:**

- Check the capability route before composing the prompt.
- Use `../../remote-providers/` for hosted model-specific asset support.
- Use `../../local-models/` for local backend-specific modality behavior.
- Fall back to text-only prompting when the backend lacks the required asset support.

## Cache directory and stale-cache behavior

**Symptom:** a cached helper returns stale results, or cache writes go to the wrong place.

**Cause:** the cache directory, version, or decorated function changed without clearing the old cache.

**Fix:**

- Set `OUTLINES_CACHE_DIR` explicitly for reproducible runs.
- Use `outlines.clear_cache()` after changing a cached function's behavior or output shape.
- Use `cache_disabled()` while debugging or when a path should stay stochastic.
- Use `disable_cache()` only when you intentionally want to suppress caching for the current session.

```python
from outlines.caching import cache_disabled

with cache_disabled():
    # rerun a prompt assembly helper or probe a stochastic path
    pass
```

## Generated-code safety

**Symptom:** a prompt or model output looks like Python, shell, or notebook code and someone wants to execute it.

**Cause:** prompt workflows often produce plausible code-shaped text, but text is not a trusted program.

**Fix:**

- Do not use `eval`, `exec`, `compile`, shell interpolation, or notebook execution on generated text.
- Keep parsing constrained to JSON, regex, or schema validators.
- If code execution is genuinely required, move it into a separate approved sandbox workflow.

## Application returns an unexpected result shape

**Symptom:** the prompt renders correctly, but the application output is not the expected type.

**Cause:** the output type, model capability, or prompt instructions do not agree.

**Fix:**

- Validate the template independently.
- Confirm the selected backend can satisfy the output type.
- Route structured outputs through the sibling structured-generation skill.
- Reduce prompt ambiguity and keep the output contract narrow.

## Self-consistency loops never converge

**Symptom:** repeated sampling produces many distinct answers and no stable winner.

**Cause:** the prompt is too open-ended, the reducer is under-specified, or the answer space is too large.

**Fix:**

- Reduce the answer space with a tighter prompt or a schema.
- Bound the number of samples.
- Use deterministic parsing and a clear majority/tie-break rule.
- When the task is ambiguous, capture the ambiguity instead of forcing a false consensus.
