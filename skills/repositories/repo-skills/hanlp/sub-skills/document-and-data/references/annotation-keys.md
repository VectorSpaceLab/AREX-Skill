# Annotation Keys

Core keys: `tok` tokenization, `pos` POS tags, `lem` lemmas, `fea` UD features, `ner` named entities, `dep` dependency parse, `con` constituency parse, `srl` semantic role labeling, `sdp` semantic dependency parse, and `amr` abstract meaning representation.

Common suffixes distinguish standards or variants: `tok/fine`, `tok/coarse`, `pos/ctb`, `pos/pku`, `pos/863`, `pos/ud`, `ner/msra`, `ner/pku`, and `ner/ontonotes`.

NER and SRL spans use token offsets with inclusive `begin` and exclusive `end`. Dependency heads use integer head indices with root as `0`. Use exact keys when the downstream consumer requires a specific standard.
