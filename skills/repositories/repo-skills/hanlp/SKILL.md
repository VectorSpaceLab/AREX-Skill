---
name: hanlp
description: "Routes agents using HanLP for multilingual NLP via native Python
  models, RESTful clients, Document outputs, custom dictionaries, and training
  or repository-maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# HanLP

Use this repo skill when a task involves HanLP: multilingual Chinese/English/Japanese NLP, RESTful parsing, native Python pretrained models, task keys such as `tok`, `pos`, `ner`, `dep`, `srl`, `sdp`, `con`, `amr`, the `hanlp_common.Document` output format, trie/custom dictionary behavior, or maintaining/training HanLP components.

HanLP has two main use modes:

- **RESTful API**: install `hanlp-restful`, create `HanLPClient`, and call a remote service. This is lightweight and convenient, but needs a reachable service and may need auth.
- **Native Python API**: install `hanlp`, load pretrained components with `hanlp.load`, or compose `hanlp.pipeline`. This runs locally, may download model archives into `HANLP_HOME`, and can use CPU or GPU depending on the installed backend and `devices` settings.

## Start Here

- Read `references/installation-and-configuration.md` when choosing install variants, cache paths, mirrors, GPU visibility, or the minimal import check.
- Read `references/troubleshooting.md` first for install/import, model download, GPU, RESTful service, or task-key errors.
- Read `references/repo-provenance.md` before deciding whether this skill matches a current checkout or should be refreshed.
- Run `scripts/check_hanlp_environment.py` for a source-free import, version, optional backend, and environment-variable diagnostic.

## Install and Minimal Check

For RESTful client use:

```bash
python -m pip install hanlp-restful
python -c "from hanlp_restful import HanLPClient; print(HanLPClient)"
```

For native local models:

```bash
python -m pip install hanlp
python -c "import hanlp; print(hanlp.__version__); print(len(hanlp.pretrained.ALL))"
```

Optional native extras are separate: `hanlp[tf]` for TensorFlow/fastText paths, `hanlp[amr]` for AMR dependencies, and `hanlp[full]` for all optional groups. Do not install broad extras unless the requested workflow needs them.

## Route by Task

| User task | Read |
| --- | --- |
| Load local pretrained models, pick model identifiers, use `hanlp.load`, set `tasks`/`skip_tasks`, choose CPU/GPU devices, split sentences, or compose a `hanlp.pipeline` | `sub-skills/native-workflows/SKILL.md` |
| Use the hosted or self-hosted RESTful API from Python, Java, or Go; build parse payloads; handle auth, language, timeout, verify, or HTTP errors | `sub-skills/restful-clients/SKILL.md` |
| Interpret or validate HanLP inputs and outputs: `Document`, JSON task keys, token nesting, `pretty_print`, `to_conll`, span formats, or annotation labels | `sub-skills/document-and-data/SKILL.md` |
| Use deterministic sentence rules, `Trie`, `TrieDict`, custom tokenization dictionaries, `dict_force`, `dict_combine`, or POS/NER dictionary overlays | `sub-skills/rules-and-trie/SKILL.md` |
| Train/fine-tune components, inspect `fit`/`evaluate` APIs, install an editable checkout, run focused tests, or maintain the repository | `sub-skills/training-and-development/SKILL.md` |

## Common Routing Decisions

- If the user only needs quick parsing in an application and can call a service, start with `restful-clients`.
- If the user needs local execution, offline inference, model customization, or direct PyTorch/TensorFlow control, start with `native-workflows`.
- If the blocker is confusing output shape or task names such as `tok/fine`, `ner/msra`, or `dep`, start with `document-and-data` even when the output came from RESTful or native APIs.
- If the task mentions user dictionaries, gazetteers, longest-prefix matching, forced tokens, or matching spans without loading a model, start with `rules-and-trie`.
- If the task involves `save_dir`, datasets, `fit`, `evaluate`, CI tests, editable installs, or source changes, start with `training-and-development`.

## Bundled Helper Scripts

All helpers are safe by default and do not call the RESTful service, download pretrained models, train models, or mutate external state.

- `scripts/check_hanlp_environment.py`: package import, distribution, environment variable, and CPU/CUDA visibility diagnostics.
- `sub-skills/native-workflows/scripts/pipeline_smoke.py`: no-download pipeline append/copy smoke test.
- `sub-skills/native-workflows/scripts/split_sentence_smoke.py`: rule-based sentence splitting smoke test.
- `sub-skills/restful-clients/scripts/restful_payload_preview.py`: build and validate a local `/parse` JSON payload without network calls.
- `sub-skills/document-and-data/scripts/document_smoke.py`: tiny `Document` JSON/CoNLL/pretty/prefix behavior check.
- `sub-skills/document-and-data/scripts/validate_document_json.py`: lightweight HanLP-like JSON shape validator.
- `sub-skills/rules-and-trie/scripts/rules_smoke.py`: rule and string utility smoke checks.
- `sub-skills/rules-and-trie/scripts/trie_smoke.py`: trie and dictionary smoke checks.
- `sub-skills/training-and-development/scripts/inspect_training_api.py`: safe training API signature inspection.

## What This Skill Does Not Cover

- It does not prove live RESTful service availability, auth quota, or network conditions.
- It does not prove GPU acceleration unless the active environment has a GPU-enabled framework and a task explicitly verifies it.
- It does not run pretrained model downloads or long training jobs by default.
- It does not require the original HanLP source checkout for runtime use; source files, demos, and tests were distilled into bundled references and scripts.
