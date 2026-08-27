# Document API Reference

Verified methods: `Document.to_json`, `to_dict`, `to_conll(tok='tok', lem='lem', pos='pos', fea='fea', dep='dep', sdp='sdp')`, `to_pretty`, `pretty_print`, `translate`, `squeeze`, `get_by_prefix`, and `count_sentences`.

`Document` is a `dict` subclass:

```python
from hanlp_common.document import Document
doc = Document(tok=[["晓美焰", "来到", "北京", "。"]], pos=[["NR", "VV", "NR", "PU"]])
print(doc.to_json())
print(doc.count_sentences())
```

Use exact keys when annotation standards matter, and `get_by_prefix('ner')` or similar when any suffix is acceptable. `pretty_print` is display-oriented; use `to_json` or `to_dict` for data exchange. `to_conll` requires token-aligned fields and dependency heads with root as `0`.
