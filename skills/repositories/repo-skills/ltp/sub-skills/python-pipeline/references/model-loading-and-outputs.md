# Model Loading and Output Handling

## Model loading decision tree

1. **No network allowed?** Use a local model path or pass `local_files_only=True` and be ready for a cache miss.
2. **Need SRL/DEP/SDP/SDPG?** Use a neural model (`LTP/tiny`, `LTP/small`, `LTP/base*`), not legacy.
3. **Need maximum speed for CWS/POS/NER only?** Use `LTP/legacy` or direct legacy-extension APIs.
4. **Private model?** Pass a token through runtime configuration, not committed code.
5. **GPU requested?** Verify torch CUDA before `ltp.to("cuda")`.

## Local model directory requirements

The high-level factory first looks for `config.json`. If it is absent, loading stops before model weights are resolved. A complete local neural model also needs the tokenizer and PyTorch weight files expected by the config. A complete legacy model directory needs the CWS/POS/NER model files named in its config.

Use the smoke script with a local path:

```bash
python scripts/ltp_pipeline_smoke.py --model-path /path/to/model --local-files-only --tasks cws,pos,ner
```

## Output normalization

| LTP field | Normalize for downstream use |
| --- | --- |
| `cws` | List of words per sentence. Preserve original text if offsets matter. |
| `pos` | Same length as words. Store alongside words. |
| `ner` | Entity tuples. Neural post-processing includes tag, text, start, end. Legacy high-level output may include tag/text unless raw format is requested. |
| `srl` | Predicate dictionaries with word index, predicate text, and argument tuples. Keep indices word-based. |
| `dep` | `{"head": [...], "label": [...]}`. Heads use root index 0 and token positions starting at 1. |
| `sdp` | Tree-like semantic dependency result shaped like DEP. |
| `sdpg` | Graph arcs. When converting, treat tuple/list entries as source, target/head, relation label. |

## CoNLL-U-like conversion notes

The bundled converter expects JSON with fields like this:

```json
{
  "cws": [["他", "叫", "汤姆", "去", "拿", "外衣", "。"]],
  "pos": [["r", "v", "nh", "v", "v", "n", "wp"]],
  "dep": [{"head": [2, 0, 2, 2, 4, 5, 2], "label": ["SBV", "HED", "VOB", "CMP", "VOB", "VOB", "WP"]}],
  "sdpg": [[]]
}
```

Then run:

```bash
python scripts/convert_ltp_output_to_conllu.py --input output.json
```

The converter writes `_` for fields LTP does not produce and uses the POS tag as `XPOS`.

## Label preservation

Do not translate or discard model labels during machine-readable processing. Keep original tags such as `nh`, `Ni`, `SBV`, or `AGT` in outputs and add human-readable glosses only as adjacent metadata.

## Handling long documents

- Split documents into sentences with `StnSplit` first.
- Batch sentences with similar lengths when possible.
- Track offsets before splitting if entity spans need to be mapped back to document text.
- Neural tokenization truncates to a configured maximum length; split long sentences before inference if complete coverage is required.
