# Custom Dictionaries

Transformer tokenizers expose two dictionary hooks:

```python
tok.dict_force = {'和服', '服务项目'}
tok.dict_combine = {'和服', '服务项目'}
```

`dict_force` performs high-priority longest-prefix matching on raw input and can force a matched string to a token sequence, for example `{'和服务': ['和', '服务']}`. Use it carefully because it can override useful model behavior.

`dict_combine` merges model-predicted token sequences. It is safer for many domain terms but cannot fix every missing raw-string match if the model did not produce compatible pieces.

For entries with spaces or tokenizer-stripped characters, use tuple keys such as `('iPad', 'Pro')`. POS and NER components can expose `dict_tags`, `dict_whitelist`, or similar component-specific hooks; verify the loaded component supports the attribute.
