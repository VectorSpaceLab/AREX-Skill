# Repo Provenance

- Skill id: `unilm`
- Source repository: Microsoft UniLM umbrella repository
- Source commit: `833df7e7832e5064a281131ee64a481afa8e5b95`
- Source branch: `master`
- Exact tag: none detected
- Working tree state at generation: dirty because `skills/` review/runtime outputs were untracked
- Remote URL: https://github.com/microsoft/unilm
- Package/version facts: representative lightweight live inspection verified `adalm` distribution version `0.0` and import module `finetune`; `unilm-v1/src/setup.py` declares `pytorch_pretrained_bert` version `0.4.0`
- Inspection environment: private research context only; no local executable, prefix, or cache paths are recorded in this public skill

## Evidence Paths

- `README.md`
- `unilm/README.md`
- `unilm-v1/README.md`
- `unilm-v1/src/setup.py`
- `unilm-v1/src/biunilm/`
- `unilm-v1/src/pytorch_pretrained_bert/`
- `s2s-ft/README.md`
- `s2s-ft/run_seq2seq.py`
- `s2s-ft/decode_seq2seq.py`
- `e5/README.md`
- `e5/mteb_beir_eval.py`
- `e5/scripts/`
- `simlm/README.md`
- `simlm/src/`
- `simlm/scripts/`
- `beit/`, `beit2/`, `beit3/`
- `dit/`
- `layoutlm/`, `layoutlmft/`, `layoutlmv2/`, `layoutlmv3/`, `layoutxlm/`
- `markuplm/`, `xdoc/`, `trocr/`, `vlmo/`, `vl-beit/`
- `kosmos-2/`, `kosmos-2.5/`
- `textdiffuser/`, `textdiffuser-2/`
- `wavlm/`, `beats/`, `speecht5/`, `speechlm/`, `valle/`, `LatentLM/`
- `Diff-Transformer/`, `YOCO/`, `deepnet/`, `longnet/`, `longvit/`, `retnet/`, `xmoe/`, `bitnet/`, `decoding/`, `PFPO/`, `ReSA/`

## Refresh Signals

Refresh this skill when the UniLM checkout adds or removes major project directories, changes native CLI flags, updates model-family READMEs, replaces legacy dependency stacks, adds self-contained examples/tests, or changes package metadata for installable subprojects.
