---
name: dataset-and-resources
description: "Create, inspect, validate, and convert Snips NLU datasets and
  reason about custom/built-in entities and language resources."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dataset and Resources

Use this sub-skill when the task is about Snips NLU dataset authoring, conversion, inspection, validation, custom entities, built-in entities, supported languages, or language resources.

This skill is for Snips NLU `0.20.2` / model format `0.20.0` behavior. It does not train engines, parse user text, persist models, download resources, or run network-backed setup.

## Route elsewhere

- Training, parsing, `SnipsNLUEngine`, `fit`, `parse`, `get_intents`, `get_slots`, `persist`, and `from_path`: use the sibling `../engine-api/SKILL.md`.
- CLI command construction or execution for `generate-dataset`, `download`, `download-entity`, `download-language-entities`, `link`, metrics, train, parse, or version commands: use `../cli-workflows/SKILL.md`.

## Operating procedure

1. Identify the input form:
   - YAML authoring documents with `type: intent` or `type: entity`.
   - JSON training datasets with root keys `language`, `intents`, and `entities`.
2. For YAML details, slot annotation syntax, implicit slot/entity behavior, and JSON schema, read `references/data-formats.md`.
3. For built-in entity names, custom entity knobs, supported languages, and resource implications, read `references/resources-and-entities.md`.
4. Validate a JSON dataset before handing it to training/API workflows:
   ```bash
   python scripts/validate_snips_dataset.py --dataset dataset.json --explain
   ```
5. Convert YAML authoring files to JSON without invoking training:
   ```bash
   python scripts/snips_yaml_to_json.py --language en intent.yaml entity.yaml --output dataset.json
   ```
6. If conversion or validation fails, diagnose using `references/troubleshooting.md`; keep fixes in the dataset files, then rerun validation.

## Key API anchors

- `Dataset.from_yaml_files(language, filenames)` converts one or more YAML files/streams into a dataset object whose `.json` property is the JSON training format.
- `validate_and_format_dataset(dataset)` accepts either a dataset object or JSON-like dict, checks the authoring schema, normalizes custom entity data, and returns a formatted dataset with `validated: true`.
- `load_resources(name, required_resources=None)` loads language resources by language/resource name, resource package, or directory path; do not download implicitly from this sub-skill.

## Safety notes

- The bundled scripts only read provided dataset files and optionally write a JSON output file; they never train a model or download resources.
- `snips_yaml_to_json.py` refuses to overwrite an existing output file unless `--overwrite` is provided.
- If a built-in entity or language resource is missing, route setup/download command work to `../cli-workflows/SKILL.md` instead of attempting network access here.
