# Native API Reference

Verified signatures include `hanlp.load(save_dir: str, verbose=None, **kwargs)`, `hanlp.pipeline(*pipes)`, `Pipeline.append(component, input_key=None, output_key=None, **kwargs)`, `Pipeline.__call__(doc=None, **kwargs)`, `MultiTaskLearning.predict(data, tasks=None, skip_tasks=None, ...)`, and `TorchComponent.load(save_dir, devices=None, verbose=True, **kwargs)`.

`hanlp.load` accepts a predefined identifier, URL, or local model directory. Predefined identifiers are registered in `hanlp.pretrained.ALL` from modules under `hanlp.pretrained`.

```python
import hanlp
model = hanlp.load('CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_SMALL_ZH', devices=-1)
doc = model(['商品和服务', '研究生命'], tasks='tok/fine')
print(doc['tok/fine'])
```

Local MTL inputs are sentence-level. Use `tasks` to limit outputs and `skip_tasks='tok*'` with nested token lists when reusing user tokenization. Loading may download model archives and Hugging Face assets, so state cache/network assumptions first.

`hanlp.pipeline()` composes callables:

```python
import hanlp
from hanlp.utils.rules import split_sentence
pipe = hanlp.pipeline().append(split_sentence, output_key='sentences')
print(pipe('Go to hankcs.com. Yes.')['sentences'])
```

Use `devices=-1` for CPU checks and GPU devices only after verifying a compatible GPU-enabled backend.
