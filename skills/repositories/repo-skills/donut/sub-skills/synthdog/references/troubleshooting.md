# SynthDoG Troubleshooting

## Purpose

Read this when `synthtiger` fails to import, the rendered config points at missing resources, or the CLI does not produce the expected split/metadata layout.

## Quick recovery table

| Symptom | Likely cause | Recovery | Stop when |
| --- | --- | --- | --- |
| `ModuleNotFoundError: synthtiger` or `command not found: synthtiger` | The active environment does not have SynthDoG installed | Install `synthtiger` in the active environment and re-run `python -c "import synthtiger"` before trying the CLI again | You cannot install into the current environment and need a new one |
| `ModuleNotFoundError: pytweening`, `ImportError` around `imgaug`, or OpenCV/Numpy mismatch noise | A dependency version drifted from the verified SynthDoG stack | Reinstall the known-compatible stack, then run `pip check` again | The environment manager cannot resolve a compatible wheel set |
| `FileNotFoundError` for background, paper, corpus, or font paths | The config still points at missing resource directories | Re-render the config with `scripts/render_config.py` and explicit resource paths, then confirm the files exist | You do not have any usable font/corpus/background assets |
| CLI complains about the template path or config path | The command order is wrong or the `SynthDoG` class name was omitted | Run from the sub-skill root with `synthtiger -o OUT -c COUNT -w WORKERS -v scripts/template.py SynthDoG rendered.yaml` | The CLI syntax is still unclear after copying the exact command |
| Generated text is blank, tiny, or obviously truncated | Missing glyphs, a weak corpus, or layout settings that are too tight | Use language-matching fonts, a longer corpus, and then tune `text_scale`, `fill`, `max_row`, `max_col`, or `stack_spacing` | The corpus/font pair cannot render the selected language |
| macOS worker crashes or fork-safety warnings | The source README's macOS fork-safety caveat was not set | Export `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` before running `synthtiger` | You cannot change the macOS process model |
| Only one split directory appears in a tiny smoke run | The split is random and the sample count is too small | Increase `-c` if you need to observe all of `train/`, `validation/`, and `test/` | You only need a smoke run and not split coverage |
| `metadata.jsonl` keeps growing after reruns | The template appends metadata lines and does not clear old output | Write to a fresh output directory or clean the split directories before rerunning | You are intentionally appending to the same dataset |

## What to check first

1. Confirm the environment has `synthtiger`, NumPy, OpenCV, and `pytweening`; the root `scripts/runtime_smoke.py --check synthdog` command checks these imports.
2. Confirm the rendered config points at the resource directories you actually have.
3. Confirm the command is run from the sub-skill root, not from a random working directory.
4. Confirm the output directory is writable and fresh enough for the metadata file you want.

## When to escalate

- Escalate to the root troubleshooting file for shared install/import issues in the broader Donut stack.
- Escalate to the training sub-skill if the generated data is ready and the user wants to fine-tune on it.
- Stop and ask for assets or permissions when the missing piece is an unavailable font set, corpus, or writable output directory rather than a command typo.
