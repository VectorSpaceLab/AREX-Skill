---
name: deployment-and-contrib
description: "Use docTR deployment templates, demo surfaces, contrib utilities,
  Docker images, optional extras, and Hugging Face Hub workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# deployment-and-contrib

Use this sub-skill when a docTR task is about an optional surface around the core OCR package rather than a plain `DocumentFile -> predictor -> result` workflow:

- exposing OCR/KIE through a FastAPI service;
- adapting the Streamlit demo flow;
- choosing Docker images or Docker GPU settings;
- installing or debugging optional `html`, `viz`, or `contrib` extras;
- using `doctr.contrib.ArtefactDetector`;
- loading from or sharing to the Hugging Face Hub.

Start by deciding whether the user actually needs a service/demo. For scripts, notebooks, batch jobs, or one-off research experiments, route them to the package API sub-skills instead of starting a long-lived service.

## Read order

1. For API, demo, and Docker deployment shape, read [references/api-and-demo.md](references/api-and-demo.md).
2. For optional extras, `ArtefactDetector`, and Hugging Face Hub loading/pushing, read [references/contrib-and-hub.md](references/contrib-and-hub.md).
3. For missing extras, MIME/route errors, GPU/Docker issues, and Hub authentication failures, read [references/troubleshooting.md](references/troubleshooting.md).

## Route away

- Use the core OCR/KIE sub-skill for normal `ocr_predictor`/`kie_predictor` Python API work, predictor parameters, batching, and result interpretation.
- Use the document IO/export sub-skill for `DocumentFile`, HTML input, visualization/export methods, and output object semantics.
- Use the models/customization sub-skill for architecture selection, model factories, ONNX export, precision/compile/device optimization, and custom weights outside Hub packaging.
- Use the CLI/scripts sub-skill for installed `doctr-cli` and bundled batch helpers.
- Use the datasets/training sub-skill before Hub publishing when the model still needs training, evaluation, or artifact validation.

## Safety boundaries

- Do not start a web server, Streamlit app, Docker container, browser session, interactive Hub login, or Hub push unless the user explicitly asks for that side effect.
- Do not ask for, echo, save, or invent credentials. If a Hub operation needs authentication, stop and ask the user to provide an already-configured token/session or to approve an interactive login.
- Do not claim full service, Docker, GPU, or Hub verification from static inspection alone. Treat the recipes here as deployment guidance until the requested runtime check is actually run.
- Keep service ports, file-size limits, authentication, concurrency, and model cache behavior explicit when moving from a demo/template to production.
