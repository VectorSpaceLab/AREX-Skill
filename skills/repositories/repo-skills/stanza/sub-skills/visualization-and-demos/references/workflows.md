# Workflows

## 1. Build a static CoNLL-U review page
1. Feed annotated CoNLL-U to `scripts/render_conllu_html.py` from stdin or a file.
2. Keep the input as already-annotated data; do not try to download models here.
3. Review the generated HTML for sentence structure, heads, deprels, and NER.
4. If the input is malformed, hand it to `documents-and-conllu` for validation instead of forcing this helper to guess.

## 2. Adapt a notebook demo into a script
1. Identify the pure transformation logic from the notebook cells.
2. Replace notebook-only calls such as `display`, `components.html`, or widget state with plain functions and explicit arguments.
3. Keep output generation self-contained: write HTML to stdout or a file path instead of relying on notebook rendering.
4. Make model downloads and pipeline creation explicit, or route those pieces to `pipelines-and-resources`.
5. Treat `demo/pipeline_demo.py` as a structural reference only; it still downloads models and runs pipeline inference.

## 3. Reuse the browser visualizers safely
1. Use the dependency and NER visualizers when spaCy/displaCy is present.
2. Use the Semgrex and Ssurgeon visualizers only when the Streamlit/IPython presentation layer is available.
3. Treat the demo server and its local CSS/JS/font assets as reference material only; do not copy them verbatim.
4. Keep the browser/server prerequisites visible to the user so the workflow does not silently depend on a notebook.

## 4. Decide the correct route
- Need new annotations or model access? `pipelines-and-resources`
- Need Java CoreNLP or server-driven annotations? `corenlp-client`
- Need schema checks or malformed CoNLL diagnosis? `documents-and-conllu`
- Need a quick visual review without notebooks or downloads? this sub-skill

## Notebook examples to adapt, not reopen
- `demo/CONLL_Dependency_Visualizer_Example.ipynb`
- `demo/Dependency_Visualization_Testing.ipynb`
- `demo/NER_Visualization.ipynb`
- `demo/Stanza_Beginners_Guide.ipynb`
- `demo/Stanza_CoreNLP_Interface.ipynb`
- `demo/semgrex visualization.ipynb`

## Demo-server reference only
`stanza/pipeline/demo/demo_server.py` shows the legacy HTML demo shape and its adjacent static assets (`stanza-brat.css`, `stanza-brat.js`, `stanza-parseviewer.js`, `loading.gif`, fonts, logo, favicon). Use that only as structure evidence; do not copy the assets into a new skill.
