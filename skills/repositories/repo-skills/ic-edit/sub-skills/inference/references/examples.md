# Example Inputs

These bundled images are copied from the ICEdit repository evidence and are safe to use as local smoke-test inputs.

| File | Size | Why it is useful |
| --- | --- | --- |
| `references/assets/girl.png` | 512×768 | Clean starter image for prompt edits |
| `references/assets/boy.png` | 512×773 | Shows that the helper does not need a height that is a multiple of 8 when width is already 512 |
| `references/assets/kaori.jpg` | 2000×2000 | Exercises the automatic resize-to-512 path |

Recommended starter prompt:

> Make her hair dark green and her clothes checked.

That matches the README example and works well for a first smoke test.
