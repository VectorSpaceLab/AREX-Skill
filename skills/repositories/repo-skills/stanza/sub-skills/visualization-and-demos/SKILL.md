---
name: visualization-and-demos
description: "Safely adapt Stanza demos and visualization workflows into scripts
  or static review artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# visualization-and-demos

Use this sub-skill when you need to turn Stanza demo or visualizer behavior into a safe runtime workflow without reopening notebooks or copying browser assets.

## Covers
- adapting notebook-driven demos into plain scripts or reusable functions
- using dependency, NER, Semgrex, and Ssurgeon visualizers at a high level
- generating static HTML review artifacts from CoNLL-U input

## Do not use for
- CoreNLP server setup or Java client behavior; route to `corenlp-client`
- model downloads or pipeline inference; route to `pipelines-and-resources`
- CoNLL-U validation or document surgery; route to `documents-and-conllu`

## Primary helper
- `scripts/render_conllu_html.py` reads CoNLL-U from stdin or a file and writes a self-contained HTML review page.

## Evidence distilled
- `demo/pipeline_demo.py`
- the notebook set in `demo/`
- `stanza/pipeline/demo/demo_server.py` and its local static assets, reference only
- `stanza/utils/visualization/*.py`
- `setup.py` extras for `visualization` and `matplotlib`
- the README Colab/demo section

## Follow the references
- `references/optional-dependencies.md`
- `references/workflows.md`
- `references/troubleshooting.md`
