# Pretrained Models

HanLP exposes model constants under `hanlp.pretrained.<family>` and registers them in `hanlp.pretrained.ALL`. Common families include `mtl`, `tok`, `pos`, `ner`, `dep`, `constituency`, `srl`, `sdp`, `amr`, `eos`, `classifiers`, `sts`, `word2vec`, `fasttext`, and `glove`.

Choose MTL models when the user wants several annotations in one pass. Choose single-task models and `hanlp.pipeline` when task-specific model choice or custom composition matters. RESTful service outputs may differ from local native outputs because model versions and settings can differ.

Always confirm language, task keys, cache/network readiness, optional dependencies, and CPU/GPU backend before loading a model. Some model licenses are research-only or non-commercial; verify license constraints before production use.
