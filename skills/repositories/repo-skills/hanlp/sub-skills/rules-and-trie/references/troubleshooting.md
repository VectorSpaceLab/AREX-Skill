# Rules and Trie Troubleshooting

- Expected all overlaps but got segmentation-like matches: use `Trie.parse`, not `TrieDict.tokenize`.
- Expected longest segmentation but got overlaps: use `Trie.parse_longest` or `TrieDict`.
- `dict_combine` did not merge a phrase: inspect model output; use `dict_force` only if raw forcing is truly needed.
- Entry with spaces fails: use tuple entries.
- Dictionary attribute missing: the loaded component may not expose that hook.
- Rule-based `split_sentence` is deterministic, not a trained EOS model; load an EOS model only after cache/network readiness is explicit.
