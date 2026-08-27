# Data and model zoo notes

face.evoLVe's public data and model zoo references are external artifacts.
Large datasets, pair archives, checkpoints, exported PaddlePaddle models, and
videos are not bundled with this skill. Before asking a user to fetch anything,
confirm access rights, license terms, local storage, and whether Google Drive,
Baidu Drive, AI Studio, or another host is permitted in the user's environment.

## Dataset artifact families

Use the dataset zoo to identify an artifact family, not as a guarantee that the
artifact is already available. Keep the downloaded folder name close to the
published dataset/version name so training and validation notes remain clear.

Common training-scale or identity-folder artifacts:

- `CASIA-WebFace` raw/clean/aligned variants.
- `MS-Celeb-1M` clean and `MS-Celeb-1M_Align_112x112` variants.
- `Vggface2` clean/aligned variants and `Vggface2_FP` for frontal-profile
  verification.
- Additional large or specialized face datasets such as DeepGlint, WebFace260M,
  UTKFace, BUAA-VisNir, CASIA NIR-VIS 2.0, Oulu-CASIA, and face anti-spoofing
  datasets are listed externally and may have stricter access terms.

Common validation-pair artifacts:

- `LFW` / `lfw`
- `CFP_FF` / `cfp_ff`
- `CFP_FP` / `cfp_fp`
- `AgeDB-30` / `agedb_30`
- `CALFW` / `calfw`
- `CPLFW` / `cplfw`
- `Vggface2_FP` / `vgg2_fp`

For validation, the expected local artifact is not just images: each benchmark
needs a `bcolz` carray directory named as above and a matching
`<name>_list.npy` file.

## Model artifact families

The model zoo examples center on face.evoLVe face-recognition backbones and
margin heads:

- PyTorch examples include IR-50 and IR-152 backbones with ArcFace and Focal
  loss, commonly trained on `MS-Celeb-1M_Align_112x112` or a private Asia face
  dataset.
- Other supported PyTorch training terminology includes IR/IR-SE/ResNet
  backbones, ArcFace/CosFace/SphereFace/Am_softmax heads, and Focal/Softmax
  losses.
- PaddlePaddle examples include ResNet-50/IR-style backbones with ArcFace and
  Focal loss, plus optional quantization and deployment flows.

Data preparation only decides whether the needed data or weight artifact is
present and plausibly named. Route checkpoint loading, feature extraction, and
performance verification to `feature-extraction-verification`; route training
config changes to `pytorch-training` or `paddle-workflows`.

## Expected local artifact shapes

- **Training images:** identity folders with image files directly inside each
  class folder. PyTorch may use `<DATA_ROOT>/imgs/<identity>/...`; PaddlePaddle
  uses the configured root directly.
- **Validation pairs:** `bcolz` carray directory plus `<name>_list.npy` per
  benchmark.
- **PyTorch checkpoints:** backbone/head checkpoint files supplied by the user or
  produced by training. Data preparation does not create or verify checkpoint
  contents.
- **PaddlePaddle deployment artifacts:** exported `.pdmodel`/`.pdiparams` files
  for Paddle Inference or `.nb` files for Paddle Lite. These are deployment
  inputs, not training data.

## External download cautions

- Do not embed cloud-drive credentials, passwords, cookies, or bypass logic in a
  skill or helper script.
- Some README entries mention passwords or private-contact terms; treat those as
  user-provided access decisions, not automated steps.
- Verify checksums or at least folder/file counts when the source provides them;
  otherwise use the bundled folder validator and validation-pair naming checks.
- Watch storage budgets: MS-Celeb-1M, VggFace2, DeepGlint, and WebFace260M scale
  to hundreds of thousands or millions of images.
- If a dataset license forbids redistribution or automated mirroring, stop and
  ask the user for an approved local artifact instead of trying alternate links.
