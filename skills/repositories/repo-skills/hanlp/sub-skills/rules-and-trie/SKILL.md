---
name: rules-and-trie
description: "Guides HanLP deterministic rules, sentence and string utilities,
  Trie/TrieDict matching, and model-backed custom dictionary overlays."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Rules And Trie

Use this sub-skill when a task mentions deterministic sentence splitting, `hanlp.utils.rules`, `possible_tokenization`, `Trie`, `TrieDict`, `TupleTrieDict`, custom dictionaries, `dict_force`, `dict_combine`, `dict_tags`, gazetteers, or longest-prefix matching.

## Read First

- Read `references/trie-reference.md` for verified trie and dictionary APIs.
- Read `references/custom-dictionaries.md` for model-backed tokenizer/POS/NER dictionary overlays.
- Read `references/troubleshooting.md` for matching surprises, tuple keys, whitespace, and model-download boundaries.
- Run `scripts/rules_smoke.py` for no-download rules/string utility checks.
- Run `scripts/trie_smoke.py` for no-download trie and dictionary checks.

## Minimal Trie Use

```python
from hanlp_trie import Trie, TrieDict
trie = Trie({'商品': 'goods', '和服': 'kimono'})
print(trie.parse('商品和服'))
print(trie.parse_longest('商品和服'))
custom = TrieDict({'重要': 'important'})
print(custom.tokenize('第一个词语很重要'))
```

Trie and rule utilities can be verified without model downloads. Model-backed dictionary overlays such as `tok.dict_force`, `tok.dict_combine`, `pos.dict_tags`, and `ner.dict_whitelist` require a loaded pretrained component before they can change model output.
