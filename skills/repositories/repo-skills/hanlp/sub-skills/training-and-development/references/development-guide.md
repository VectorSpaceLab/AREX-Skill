# Development Guide

Editable install order for a source checkout:

```bash
python -m pip install -e plugins/hanlp_trie
python -m pip install -e plugins/hanlp_common
python -m pip install -e plugins/hanlp_restful
python -m pip install -e .
python -m pip install pytest
```

Source-free helper checks bundled with this skill:

```bash
python scripts/check_hanlp_environment.py --json
python sub-skills/native-workflows/scripts/pipeline_smoke.py
python sub-skills/native-workflows/scripts/split_sentence_smoke.py
python sub-skills/document-and-data/scripts/document_smoke.py
python sub-skills/rules-and-trie/scripts/rules_smoke.py
python sub-skills/rules-and-trie/scripts/trie_smoke.py
python sub-skills/training-and-development/scripts/inspect_training_api.py --json
```

When you are maintaining a source checkout, choose private native tests based on the edited area after installation. Safe examples for this repository include rule/string utilities, pipeline behavior, config tracking, and trie plugin tests. Run the trie plugin tests from the plugin test root or as the plugin's test directory when import collection from the top-level checkout is ambiguous.

MTL tests load pretrained models and may require downloads/cache. RESTful client tests call a live service. Training demos are not unit tests.

Use focused tests based on edited area: rules/string utilities, trie plugin, pipeline, `Document` outputs, RESTful payload construction, or training API signatures.
