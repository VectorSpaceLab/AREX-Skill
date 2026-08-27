# Workflows

## Launch the UI

1. Confirm the package imports and TeX toolchain are available.
2. Run `python -m detikzify.webui --help` if you only need the CLI surface.
3. Launch the actual UI with the chosen model and algorithm.
4. Use light mode for figure-heavy scientific material unless the user wants a dark theme.

## MCTS mode

- The UI streams candidate TikZ code while search is still running.
- Compiled images appear in the gallery after successful rendering.
- Closing a preview restores the streaming code view.
- The gallery ranks results by the underlying score used by the pipeline.

## Sampling mode

- The UI returns one synthesized output image rather than a ranked gallery.
- This is the simplest route when the user does not need search over multiple candidates.

## Common runtime choices

- Use `--lock` for a fixed-model deployment or a shared public Space.
- Use `--share` only when a public link is intentionally desired.
- Tune the timeout if the compile step is expected to be slow on large documents.
