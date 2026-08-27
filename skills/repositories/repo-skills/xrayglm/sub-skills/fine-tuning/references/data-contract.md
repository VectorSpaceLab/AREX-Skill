# XrayGLM supervised data contract

This contract describes the input consumed by `FewShotDataset` in
`finetune_XrayGLM.py`. It does not acquire, translate, deduplicate, or repair
data. Those operations belong to the repository's data-preparation route.

## Accepted JSON shape

The trainer directly iterates a **top-level array**:

```json
[
  {
    "img": "data/Xray/2_1.png",
    "prompt": "请描述这张胸部X光片。",
    "label": "心脏大小正常，未见急性心肺异常。"
  }
]
```

For interchange, the validator also unwraps an object whose `annotations`
member is an array:

```json
{"annotations": [{"img": "data/Xray/2_1.png", "prompt": "...", "label": "..."}]}
```

The wrapper is not converted by the validator. Every member still needs these
exact fields:

| Field | Required type | Meaning and constraints |
|---|---|---|
| `img` | non-empty string | Local image path. Absolute paths are used as-is; relative paths are resolved against the declared image base directory. |
| `prompt` | non-empty string | User question/instruction. It is placed after `</img>问：` and before `\n答：`. |
| `label` | non-empty string | Supervised response. It is the target continuation and may contain Chinese text. |

Extra fields are ignored by this trainer but should be retained by upstream
provenance tooling. Blank strings, nulls, numbers, arrays, and objects do not
satisfy the contract. The validator reports all record errors in stable input
order and never edits the source file.

## Important repository mismatch

`data/Xray/openi-zh.json` in this checkout is an object with an `annotations`
array whose members use `image_id` and `caption`, not `img`, `prompt`, and
`label`. It is therefore **not directly consumable** by `FewShotDataset`, even
though `finetune_XrayGLM.sh` points at it. A data-preparation workflow must
produce the flat training contract and resolve image IDs to actual files before
this route can accept it. Do not silently alias or rewrite those fields here.

The demo file `data/demo/dataset.json` has the required three fields, but its
paths are relative to the demo-data layout (`fewshot-data/...`); pass the
corresponding image root explicitly rather than assuming the repository root.

## Path and image checks

Use the bundled checker from any working directory:

```bash
python /absolute/path/to/validate_training_records.py records.json \
  --check-images --base-dir /absolute/path/to/image/root
```

With `--check-images`, each non-empty `img` path is resolved without changing
it, opened with Pillow, and verified. Missing files and unreadable/corrupt or
unsupported images are distinct diagnostics. Without `--base-dir`, the
checker uses the directory containing the JSON file, which is deterministic but
may not be the training image root. Prefer an absolute `--base-dir` for a
launcher run from another working directory.

A valid record is not necessarily medically correct, non-duplicated, licensed,
or leakage-free. Those are upstream review obligations. Keep the original JSON
and image tree immutable during validation; write any proposed converted file
outside the input tree through the data-preparation workflow.

## Pre-training checklist

- [ ] The JSON root is an array or an `annotations` wrapper containing an array.
- [ ] Every record has non-empty string `img`, `prompt`, and `label`.
- [ ] The image root is explicit and stable for the eventual launcher process.
- [ ] Every image opens successfully and has a supported raster format.
- [ ] The labels are the intended target text, not a report or prompt accidentally
      copied into the other field.
- [ ] Dataset count and split/reuse policy are recorded; the checked-in launcher
      currently uses the same file for train and validation.
