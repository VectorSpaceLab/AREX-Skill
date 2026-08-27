# Repo provenance

Schema: `disco.repo-provenance.v1`

## Source identity

- Public project: `davidsandberg/facenet`
- Source remote: `https://github.com/davidsandberg/facenet.git`
- Commit: `096ed770f163957c1e56efa7feeb194773920f6e`
- Branch at source snapshot: `master`
- Exact tag: none found
- Source snapshot dirty state before generated skill files were written: clean
- Package/distribution metadata: none (`setup.py`/`pyproject.toml` absent); repository is used as a source-style module tree.
- Documented dependency baseline: TensorFlow `1.7`, Python `2.7` and `3.5` in CI, plus SciPy, scikit-learn, OpenCV, h5py, matplotlib, Pillow, requests, and psutil.
- Inspection dependency baseline used for skill construction: TensorFlow `1.15.5` CPU-compatible TF1 stack, because exact TensorFlow 1.7/Python 3.5 wheels are obsolete on the construction host. Runtime guidance still targets TensorFlow 1.x APIs rather than TensorFlow 2.x.

## Evidence paths

These relative paths were used as evidence for the generated operating graph:

- `README.md`
- `requirements.txt`
- `.travis.yml`
- `src/facenet.py`
- `src/lfw.py`
- `src/align/align_dataset_mtcnn.py`
- `src/align/detect_face.py`
- `src/compare.py`
- `src/classifier.py`
- `src/validate_on_lfw.py`
- `src/train_softmax.py`
- `src/train_tripletloss.py`
- `src/freeze_graph.py`
- `src/calculate_filtering_metrics.py`
- `src/decode_msceleb_dataset.py`
- `src/models/inception_resnet_v1.py`
- `src/models/inception_resnet_v2.py`
- `src/models/squeezenet.py`
- `src/models/dummy.py`
- `contributed/batch_represent.py`
- `contributed/cluster.py`
- `contributed/clustering.py`
- `contributed/export_embeddings.py`
- `contributed/face.py`
- `contributed/predict.py`
- `contributed/real_time_face_recognition.py`
- `test/triplet_loss_test.py`
- `test/center_loss_test.py`
- `test/restore_test.py`
- `test/train_test.py`
- `data/pairs.txt`
- `data/learning_rate_retrain_tripletloss.txt`
- `data/learning_rate_schedule_classifier_casia.txt`
- `data/learning_rate_schedule_classifier_msceleb.txt`
- `data/learning_rate_schedule_classifier_vggface2.txt`
- `data/images/Anthony_Hopkins_0001.jpg`
- `data/images/Anthony_Hopkins_0002.jpg`

## Intentional exclusions

- `src/generative/` experimental VAE/attribute workflows were not included in the primary operating graph because they require missing VAE definitions/checkpoints and CelebA-specific assets.
- `tmp/` and Matlab utilities were treated as historical experiments, not stable user-facing workflows.
- Network download scripts were used only as evidence for external asset requirements; they are not bundled as run-default helpers.

## Refresh guidance

Refresh this skill when the source commit changes, when a maintained fork modernizes the package for TensorFlow 2.x or packaging metadata, when pretrained model download locations change, or when alignment/training scripts are substantially rewritten.
