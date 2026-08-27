# Troubleshooting

## Missing Streamlit, spaCy, IPython, or matplotlib
**Symptom:** import errors when opening demo notebooks or browser visualizers.

**What to check:** whether the `visualization` extra or the `matplotlib` extra is installed.

**What to do:**
- use the `visualization` extra for spaCy/Streamlit/IPython-based flows
- use the `matplotlib` extra only when plots are the missing piece
- fall back to `scripts/render_conllu_html.py` if you only need a static review page

## Notebook-only assumptions
**Symptom:** code depends on notebook widgets, `display(...)`, `%matplotlib inline`, or IPython-specific helpers.

**What to do:**
- pull the actual transformation into a pure function
- feed it explicit inputs
- emit HTML or text from a normal script instead of relying on notebook state

## Demo code tries to download models
**Symptom:** a demo script reaches for `stanza.download(...)` or lazily constructs a pipeline.

**What to do:**
- make the download step explicit and move it to the pipeline/resource path
- do not hide model acquisition inside this visualization sub-skill

## Browser or server requirements are missing
**Symptom:** a Streamlit, Flask, or displaCy-based demo does nothing in a headless shell.

**What to check:** browser access, local server startup, CORS/port assumptions, and whether the presentation layer is actually running.

**What to do:**
- use a browser only when the workflow really needs an interactive UI
- otherwise generate a static HTML artifact with the bundled helper

## Missing heads or NER tags in CoNLL
**Symptom:** the rendered table shows `-` for head, deprel, or NER.

**Meaning:** the input did not carry that annotation, or the parser could not recover it.

**What to do:**
- verify the CoNLL-U source first
- remember that the HTML helper cannot invent missing annotations
- if the file is malformed, route to `documents-and-conllu`

## When to use `corenlp-client` instead
**Symptom:** you need Java Stanford CoreNLP annotations, Semgrex/Ssurgeon server behavior, or CoreNLP-specific demo bootstrap.

**What to do:** move the work to `corenlp-client` rather than extending this visualization sub-skill.
