# Prompt asset adaptations

The bundled assets are copied from the repository `scripts/` tree at commit `f6fb080ef755c37c01b7959e7560d007049510e8`, with the following small format repairs so future agents can use `Verbalizer.from_file` without the original checkout:

- `FewGLUE/{BoolQ,RTE,WiC}/manual_verbalizer.txt`: split source one-line `Yes No` text into one class line per label (`Yes`, `No`).
- `FewGLUE/CB/manual_verbalizer.txt`: split source one-line `Yes No Maybe` text into one class line per label.
- `SuperGLUE/WSC/manual_verbalizer.txt`: source file was empty; filled a minimal binary `Yes`/`No` manual verbalizer consistent with other boolean SuperGLUE prompt assets. Prefer `generation_verbalizer.txt` for WSC generation-style workflows.
- `TextClassification/{amazon,imdb}/knowledgeable_verbalizer.txt`: removed the obvious whitespace multi-word entry `one-hundred percent`; tokenizer-dependent multi-token checks remain a caller responsibility.

Generation verbalizer assets are intentionally left rule-like and may contain template expressions such as `{"meta":"choice1"}` or multi-word generated target text.
