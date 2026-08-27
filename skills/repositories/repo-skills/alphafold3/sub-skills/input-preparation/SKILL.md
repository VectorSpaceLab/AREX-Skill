---
name: input-preparation
description: "Build, validate, convert, and troubleshoot AlphaFold 3 input JSON
  files before prediction runs. Use when creating fold inputs, validating
  protein/RNA/DNA/ligand entries, converting AlphaFold Server JSON, adding
  MSAs/templates/user CCD/bonds, or explaining schema versions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold 3 Input Preparation

Use this sub-skill when the task is about constructing or checking AlphaFold 3 fold-input JSON, not about running inference or interpreting outputs.

## Route here for

- Creating `alphafold3` dialect JSON files with `name`, `modelSeeds`, `sequences`, `dialect`, and `version`.
- Validating protein, RNA, DNA, ligand, ion, MSA, template, `userCCD`, `userCCDPath`, and `bondedAtomPairs` fields.
- Converting AlphaFold Server-style fold jobs into AlphaFold 3 inputs and explaining conversion limits.
- Debugging `Input.from_json(...)` errors before invoking a prediction run.
- Checking path-relative external files such as `unpairedMsaPath`, `pairedMsaPath`, `mmcifPath`, and `userCCDPath`.

## Do not handle here

- Runtime database, model, GPU, bucket, or inference flags; route to `../running-predictions/`.
- Confidence JSON, ranking scores, mmCIF output, or result interpretation; route to `../output-interpretation/`.
- Lower-level model runner, data pipeline, or Python API integration beyond input parsing; route to `../python-apis/`.

## Fast workflow

1. Draft the input with `dialect: "alphafold3"` and `version: 4` unless compatibility with an older saved input is required.
2. Keep one prediction job per AlphaFold 3 JSON file. Use a top-level list only for AlphaFold Server JSON that will be converted.
3. Ensure every sequence entity has an uppercase alphabetic `id`; use a list of IDs only for identical copies.
4. Prefer explicit path fields for external content: `unpairedMsaPath`, `pairedMsaPath`, `mmcifPath`, and `userCCDPath`.
5. Validate before running prediction:

```bash
python sub-skills/input-preparation/scripts/validate_fold_input.py fold_input.json
```

## Key references

- `references/input-json.md` covers schema recipes, entity fields, conversion constraints, relative paths, and validation rules.
- `references/troubleshooting.md` maps common parser and preparation failures to fixes.
- `scripts/validate_fold_input.py` provides a safe local parser check using the installed AlphaFold 3 package.
