# Optional dependencies

Stanza keeps the browser- and notebook-oriented demo stack optional.

| Extra | Packages | Typical use | Notes |
| --- | --- | --- | --- |
| `visualization` | `spacy`, `streamlit`, `ipython` | dependency and NER visualizers, Streamlit demo flows, notebook display helpers | Needed only when you want the browser or notebook presentation layer |
| `matplotlib` | `matplotlib` | plots or figures embedded in demo notebooks and scripts | Independent from the browser visualizers |

## Practical guidance
- If you only need a static review artifact from CoNLL-U, use `scripts/render_conllu_html.py` and skip these extras.
- If a notebook or browser demo imports `spacy`, `streamlit`, or `IPython.display`, the `visualization` extra is the first thing to check.
- If a demo only fails because plotting is missing, install or enable the `matplotlib` extra instead of pulling in the browser stack.
- These extras do not replace CoreNLP, model downloads, or pipeline inference.

## Evidence points
- `setup.py` defines the `visualization` and `matplotlib` extras.
- The visualization modules and Streamlit app rely on these optional packages.
- The notebook demos are historical references for presentation patterns, not required runtime dependencies.
