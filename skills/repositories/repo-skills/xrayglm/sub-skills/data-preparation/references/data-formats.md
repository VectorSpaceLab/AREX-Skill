# XrayGLM data formats

## 1. OpenI annotation wrapper

The source wrapper is a JSON object with one required top-level field:

```json
{
  "annotations": [
    {
      "image_id": "162_1",
      "caption": "A radiology report or translated report."
    }
  ]
}
```

`annotations` must be an array. Every `image_id` and `caption` must be a
non-empty string. Image IDs are keys, not list positions, and must be unique.
The English wrapper (`data/openi-en.json`) and Chinese wrapper
(`data/Xray/openi-zh.json`) preserve this shape. A wrapper is accepted by the
validator, but the fine-tuning loader does not consume it directly.

## 2. Training-record array

The fine-tuning input is a top-level JSON array. Each item must contain these
non-empty string fields:

```json
[
  {
    "img": "./data/Xray/162_1.png",
    "prompt": "通过这张胸部X光影像可以诊断出什么？",
    "label": "根据X射线图像，心脏大小正常。"
  }
]
```

Additional fields are preserved by the merge helper, but are not needed by the
repository's `FewShotDataset`. `img` is opened as a local image, so a valid
JSON schema does not prove that the file exists or is readable. Use
`validate_xray_records.py --check-images --base-dir BASE` for an existence
check. A relative path is resolved as `BASE / img`; an absolute path is used
as-is.

The demo fixture (`data/demo/dataset.json`) has the same fields but uses
`fewshot-data/...` paths. Do not rewrite those paths to X-ray paths without an
explicit dataset decision.

## 3. Caption JSON for merging

`merge_xray_records.py` accepts either the wrapper above or a list of keyed
caption objects:

```json
[
  {"image_id": "162_1", "caption": "翻译后的报告。"}
]
```

The default merge key for records is the stem of `img`, so
`./data/Xray/162_1.png` maps to `162_1`. The default caption key is
`image_id`; the default source field is `caption`; the destination field is
`label`. Use `--record-key`, `--caption-key`, `--caption-field`, or
`--label-field` when a deliberately different schema is in use. Duplicate keys
always fail. The default requires equal item counts and equal key sets. The
explicit `--allow-length-mismatch` option allows a keyed subset but still
rejects unknown caption keys and retains unmatched records unchanged.

## 4. Deterministic prompts

The original fixed prompt is:

```text
通过这张胸部X光影像可以诊断出什么？
```

The original random script's six choices, in deterministic index order, are:

0. `通过这张胸部X光影像可以诊断出什么？`
1. `这张图片的背景里有什么内容？`
2. `详细描述一下这张图片`
3. `看看这张图片并描述你注意到的内容`
4. `请提供图片的详细描述`
5. `你能为我描述一下这张图片的内容吗？`

`convert_xray_json.py --prompt-index N` applies one choice uniformly to all
converted records. `--prompt TEXT` overrides the index. There is no random
seed hidden in the helper.

## 5. Markdown output

Converter Markdown output is a presentation/export format, not a training
input:

```markdown
## 162_1

翻译后的报告。
```

It contains image-ID headings and caption text. Converting it back to records
is intentionally not implemented: headings and free text can be edited or
reflowed, so a keyed JSON source is safer for merges.
