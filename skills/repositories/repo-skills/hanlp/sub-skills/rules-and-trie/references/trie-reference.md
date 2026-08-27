# Trie and Rule Reference

Verified signatures include `Trie(tokens=None)`, `Trie.parse(text)`, `Trie.parse_longest(text)`, `Trie.items`, `TrieDict.tokenize`, `TrieDict.split`, `TrieDict.split_batch`, `TrieDict.merge_batch`, `TupleTrieDict`, `split_sentence(text, best=True)`, `possible_tokenization(text)`, and `split_long_sentence_into`.

`Trie.parse` returns all matches including overlaps. `Trie.parse_longest` returns non-overlapping longest-prefix matches. `TrieDict.tokenize` uses longest-prefix matching and is the interface used by HanLP dictionary integrations.

Use `TupleTrieDict` for token-tuple keys, especially when spaces or tokenizer normalization make plain strings ambiguous.
