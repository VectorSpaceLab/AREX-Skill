---
name: facenet
description: "Use davidsandberg/facenet for TensorFlow 1.x face recognition
  workflows: MTCNN alignment, embeddings, classification, LFW evaluation,
  training, and model export."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Facenet Repo Skill

Use this skill when a task involves David Sandberg's TensorFlow 1.x FaceNet repository: aligning face images with MTCNN, extracting embeddings, comparing faces, training an SVM classifier, evaluating on LFW pairs, training FaceNet models, or exporting checkpoints to frozen graphs.

## First checks

1. Treat Facenet as a source-style TensorFlow 1.x project, not a modern packaged library with console entry points.
2. Prefer a Python environment that can import TensorFlow 1.x APIs (`tf.Session`, `tf.Graph`, `tf.train`, and `tf.contrib.slim`). TensorFlow 2.x without compatibility shims is not enough.
3. Ensure Facenet modules are importable as modules such as `facenet`, `lfw`, `compare`, `classifier`, `train_softmax`, `train_tripletloss`, `freeze_graph`, `align.detect_face`, and `models.inception_resnet_v1`.
4. Run [`scripts/check_facenet_environment.py`](scripts/check_facenet_environment.py) to verify imports, TensorFlow version, and common dependency availability before planning a workflow.
5. Read [`references/compatibility-and-install.md`](references/compatibility-and-install.md) when installing or debugging the old TensorFlow/Python dependency stack.

## Install/inspect

For faithful historical execution, use the repository's documented TensorFlow 1.7/Python 2.7 or 3.5 environment. On modern hosts, use an isolated Python 3.7-era environment with a compatible TensorFlow 1.x build, NumPy/SciPy/scikit-learn/OpenCV/h5py/Pillow, and a compatible `protobuf<3.20`; do not install into the interpreter running the agent. Because this repo has no packaging metadata, make its source modules importable before running module-style commands. The root checker is the minimum read-only verification:

```bash
python scripts/check_facenet_environment.py --json
```

## Route by task

- **Dataset layout, image preprocessing, and MTCNN alignment**: read [`sub-skills/data-and-alignment/SKILL.md`](sub-skills/data-and-alignment/SKILL.md) for class-folder datasets, `pairs.txt` basics, `prewhiten`/crop/flip behavior, and alignment command construction.
- **Embeddings, comparison, classifiers, and clustering**: read [`sub-skills/embeddings-and-classification/SKILL.md`](sub-skills/embeddings-and-classification/SKILL.md) for model-backed embedding extraction, `compare`, SVM classifier, `.npy` exports, DBSCAN, and contributed recognition examples.
- **LFW and verification metrics**: read [`sub-skills/evaluation/SKILL.md`](sub-skills/evaluation/SKILL.md) for `validate_on_lfw`, pair-file validation, ROC/VAL/FAR/AUC/EER interpretation, and fixed-standardization warnings.
- **Training and model definitions**: read [`sub-skills/training/SKILL.md`](sub-skills/training/SKILL.md) for softmax/triplet training commands, model definitions, loss functions, learning-rate schedules, logging, and checkpoint outputs.
- **Model files, checkpoints, and frozen graphs**: read [`sub-skills/model-export-and-checkpoints/SKILL.md`](sub-skills/model-export-and-checkpoints/SKILL.md) for accepted model path formats, `load_model`, checkpoint selection, tensor names, and `freeze_graph` workflows.

## Common Facenet objects and conventions

- A class-folder dataset is `data_dir/person_name/image.ext`; labels are assigned by sorted directory order.
- The main embedding tensor is usually `embeddings:0`, input images are `input:0`, and inference mode is controlled by `phase_train:0`.
- A checkpoint model directory must contain exactly one `.meta` file plus checkpoint state or `model-*.ckpt-*` files.
- A frozen graph is a `.pb` file that `facenet.load_model` imports directly.
- Pretrained models named in the README commonly use image size `160`; newer 2018 models require fixed image standardization for comparable LFW results.

## Default handoff order

For a new end-to-end request, use this order unless the user already supplies validated artifacts:

1. Run the environment checker and confirm TF1 imports.
2. Validate the class-folder or LFW data layout.
3. Inspect the checkpoint directory or frozen graph signature.
4. Build the narrowest workflow command with the owning sub-skill helper.
5. Run a bounded help/fixture/model smoke before any long, networked, or hardware-interactive job.
6. Record output directories, model path, image size, standardization mode, batch size, and seed so later comparisons are reproducible.

If a request crosses multiple routes, keep each artifact explicit: raw data, aligned data, model/checkpoint, classifier pickle, embeddings, metrics, and logs should not be silently mixed.

## Safety and scope

- Full training, LFW benchmarks, and pretrained comparison usually require external datasets or model downloads. Treat them as skip-network or skip-expensive unless the user supplies assets and approves runtime cost.
- Webcam recognition in contributed scripts needs a camera/display plus hard-coded model/classifier assumptions. Document it or adapt it carefully; do not start an infinite webcam loop as a smoke test.
- Do not use TensorFlow 2.x behavior to infer Facenet correctness without checking TF1 compatibility.
- The generated skill excludes the experimental VAE/generative branch and broad `tmp/` experiments unless the user explicitly asks for those historical utilities.

## References

- [`references/repo-provenance.md`](references/repo-provenance.md) records the source commit, evidence paths, and generation baseline.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) is structured metadata for managed repo-skill routing.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting install/import/model/data failures.
