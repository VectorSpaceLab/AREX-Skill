# Face ID Loss Reference

Evidence used: `models/face_features.py`, `models/mobilefacenet.py`, `models/UGATIT_sadalin_hourglass.py`, and the README training notes.

## Purpose

The face-ID loss keeps the generated cartoon image close to the source photo in identity space. The trainer computes:

- `G_id_loss_A = facenet.cosine_distance(real_A, fake_A2B)`
- `G_id_loss_B = facenet.cosine_distance(real_B, fake_B2A)`

The result is a per-sample cosine-distance tensor where smaller values mean closer identity embeddings.

## FaceFeatures contract

`FaceFeatures(weights_path, device)`:

- instantiates `MobileFaceNet(512)`
- moves the model to the requested device
- loads the weight file with `torch.load(weights_path)`
- sets the model to eval mode

`FaceFeatures.infer(batch_tensor)` expects an input tensor shaped `(N, 3, H, W)` and applies the same fixed crop that the trainer uses.

### Crop and resize path

The crop is centered and proportional to the input size:

- `top = int(h / 2.1 * (0.8 - 0.33))`
- `bottom = int(h - (h / 2.1 * 0.3))`
- `size = bottom - top`
- `left = int(w / 2 - size / 2)`
- `right = left + size`

The cropped tensor is then resized to `112 × 112` with bilinear interpolation and `align_corners=True`.

## MobileFaceNet embedding contract

`MobileFaceNet(512)` returns a 512-dimensional feature vector per sample.

The model path is:

1. convolutional feature extraction
2. flattened projection
3. batch normalization
4. `l2_norm`

The final embedding is already L2-normalized, so the vector norm should be close to 1.0 for each sample.

## Validation checks

A safe smoke check should confirm:

- the cropped tensor can be resized to `112 × 112`
- the embedding shape is `(N, 512)`
- embedding norms are close to 1
- the cosine-distance of identical embeddings is close to 0

## Asset note

`models/model_mobilefacenet.pth` is required for this path. If the asset is missing, the face-ID path cannot be verified and should be reported as unavailable rather than guessed.

