# Repository Provenance

## Purpose

Read this before deciding whether this Flair skill is current for a checkout or installed package. If the current repo commit, package version, public exports, model/dataset APIs, or documented workflows differ materially from this snapshot, refresh the skill from repository evidence before relying on exact details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T00:00:00Z",
  "repository": {
    "name": "flair",
    "remote_url": "https://github.com/flairNLP/flair.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "d4ea3777998ba67bfbe6b6b8359e024dcf673c3e",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "distribution_name": "flair",
      "import_names": ["flair"],
      "version": "0.15.1",
      "requires_python": ">=3.9"
    }
  ],
  "evidence": {
    "source_roots": [
      "flair/",
      "flair/data.py",
      "flair/datasets/",
      "flair/embeddings/",
      "flair/models/",
      "flair/nn/",
      "flair/trainers/",
      "flair/tokenization.py",
      "flair/splitter.py",
      "flair/training_utils.py",
      "flair/distributed_utils.py"
    ],
    "package_metadata": [
      "setup.py",
      "pyproject.toml",
      "requirements.txt"
    ],
    "docs": [
      "README.md",
      "docs/tutorial/tutorial-basics/",
      "docs/tutorial/tutorial-embeddings/",
      "docs/tutorial/tutorial-training/",
      "docs/tutorial/tutorial-hunflair2/",
      "resources/docs/HUNFLAIR.md",
      "resources/docs/HUNFLAIR2.md",
      "resources/docs/TUTORIAL_8_MODEL_OPTIMIZATION.md",
      "resources/docs/TUTORIAL_9_TRAINING_LM_EMBEDDINGS.md",
      "resources/docs/TUTORIAL_PRODUCTION_FASTER_TRANSFORMERS.md"
    ],
    "examples": [
      "examples/README.md",
      "examples/ner/run_ner.py",
      "examples/multi_gpu/run_multi_gpu.py"
    ],
    "tests": [
      "tests/test_sentence.py",
      "tests/test_labels.py",
      "tests/test_sentence_serialization.py",
      "tests/test_tokenization.py",
      "tests/test_corpus_dictionary.py",
      "tests/test_datasets.py",
      "tests/test_trainer.py",
      "tests/test_multitask.py",
      "tests/test_language_model.py",
      "tests/test_visual.py",
      "tests/test_biomedical_entity_linking.py",
      "tests/test_datasets_biomedical.py",
      "tests/models/test_regexp_tagger.py",
      "tests/models/test_sequence_tagger.py",
      "tests/models/test_text_classifier.py",
      "tests/models/test_tars_classifier.py",
      "tests/models/test_tars_ner.py",
      "tests/models/test_relation_extractor.py"
    ],
    "scripts_adapted_or_referenced": [
      "collect_env.py",
      "examples/ner/run_ner.py",
      "examples/multi_gpu/run_multi_gpu.py"
    ],
    "installed_package_inspection": [
      "distribution metadata",
      "public imports",
      "selected constructor and method signatures",
      "CPU import and smoke behavior"
    ]
  },
  "verification_scope": {
    "required_backend": "cpu",
    "required_backend_status": "prepared and smoke-verified",
    "optional_unverified": [
      "CUDA and multi-GPU training",
      "ONNX Runtime execution providers",
      "TorchScript speedups on deployment hardware",
      "SciSpaCy model installation",
      "pyab3p abbreviation resolution",
      "large pretrained model/data downloads"
    ]
  }
}
```

## Refresh Check

Refresh this skill when any of the following is true:

- The current Git commit differs from `d4ea3777998ba67bfbe6b6b8359e024dcf673c3e` and source, docs, examples, tests, or package metadata changed outside generated `skills/` artifacts.
- The installed `flair` version is not `0.15.1`, especially if model loader IDs, dataset exports, trainer signatures, tokenizer serialization, or embedding constructors changed.
- `JsonlCorpus` / `MultiFileJsonlCorpus` exports change, making the documented import caveat stale.
- HunFlair2 linker names, default label layers, dictionaries, or pyab3p fallback behavior change.
- `ModelTrainer.train(...)` / `fine_tune(...)` signatures change, especially checkpoint or `save_model_each_k_epochs` behavior.
- Optional backends become required for the user's task and must be verified in a new environment.

## Privacy Boundary

Generated runtime skill files intentionally omit local checkout paths, temporary inspection environments, Python executables, activation commands, cache directories, and package installation locations. Public package users should install `flair`, select their own cache/output directories, and verify optional backends in their active environment.
