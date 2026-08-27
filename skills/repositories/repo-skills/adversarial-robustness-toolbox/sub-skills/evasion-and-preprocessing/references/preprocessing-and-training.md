# Preprocessing defences and adversarial training

Use this reference to add ART preprocessors and train with adversarial examples after the estimator has been wrapped correctly.

## Preprocessor chooser

| Need | Class | Import | Key parameters | Fit/predict behavior |
|---|---|---|---|---|
| Mean/std normalization | `StandardisationMeanStd` | `from art.preprocessing.standardisation_mean_std.numpy import StandardisationMeanStd` | `mean=0.0`, `std=1.0`, `apply_fit=True`, `apply_predict=True` | Differentiable gradient estimate divides by `std`; use float inputs, not unsigned integer arrays. |
| Local median smoothing for images/videos | `SpatialSmoothing` | `from art.defences.preprocessor import SpatialSmoothing` | `window_size=3`, `channels_first=False`, `clip_values=None`, `apply_fit=False`, `apply_predict=True` | Shape must be image/video; channel axis is controlled by `channels_first`. |
| Reduce bit depth | `FeatureSqueezing` | `from art.defences.preprocessor import FeatureSqueezing` | `clip_values`, `bit_depth=8`, `apply_fit=False`, `apply_predict=True` | Values are normalized to `clip_values`, rounded, then restored. |
| JPEG compression defence | `JpegCompression` | `from art.defences.preprocessor import JpegCompression` | `clip_values`, `quality=50`, `channels_first=False`, `apply_fit=True`, `apply_predict=True` | Image/video only; channel order and clipping must match estimator input. |
| Add Gaussian noise / augmentation | `GaussianAugmentation` | `from art.defences.preprocessor import GaussianAugmentation` | `sigma=1.0`, `augmentation=True`, `ratio=1.0`, `clip_values=None`, `apply_fit=True`, `apply_predict=False` | With `augmentation=True`, it increases or augments the training set and must be enabled for fit. |
| Smooth labels | `LabelSmoothing` | `from art.defences.preprocessor import LabelSmoothing` | `max_value=0.9`, `apply_fit=True`, `apply_predict=False` | Input labels should be one-hot; leaves samples unchanged. |
| Mix training samples/labels | `Mixup` | `from art.defences.preprocessor import Mixup` | `num_classes`, `alpha=1.0`, `num_mix=2`, `apply_fit=True`, `apply_predict=False` | Training augmentation; labels should match `num_classes`. |
| CutMix image augmentation | `CutMix` | `from art.defences.preprocessor import CutMix` | `num_classes`, `alpha=1.0`, `probability=0.5`, `channels_first=False`, `apply_fit=True`, `apply_predict=False` | Image training augmentation; channel order matters. |
| Cutout image augmentation | `Cutout` | `from art.defences.preprocessor import Cutout` | `length`, `channels_first=False`, `apply_fit=True`, `apply_predict=False` | Masks out square image regions during fit. |
| Thermometer encoding | `ThermometerEncoding` | `from art.defences.preprocessor import ThermometerEncoding` | `clip_values`, `num_space=10`, `channels_first=False`, `apply_fit=True`, `apply_predict=True` | Changes feature dimensionality; update estimator input expectations if used outside an estimator pipeline. |
| Total variation minimization | `TotalVarMin` | `from art.defences.preprocessor import TotalVarMin` | `prob=0.3`, `norm=2`, `lamb=0.5`, `solver='L-BFGS-B'`, `max_iter=10`, `clip_values=None`, `apply_fit=False`, `apply_predict=True` | Optimization-based and slower; start with tiny batches. |
| PixelCNN projection | `PixelDefend` | `from art.defences.preprocessor import PixelDefend` | `clip_values=(0.0, 1.0)`, `eps=16`, `pixel_cnn=None`, `batch_size=128`, `apply_fit=False`, `apply_predict=True` | Requires a compatible PixelCNN-style model; not a generic no-model defence. |

## How to attach preprocessors

### Direct callable use

```python
pre = SpatialSmoothing(window_size=3, channels_first=False, clip_values=(0.0, 1.0))
x_smooth, y_same = pre(x_images, y_labels)
```

Use direct calls for standalone data transformation, debugging, or when comparing raw and preprocessed predictions.

### Estimator-level preprocessing

ART estimators commonly support:

```python
classifier = PyTorchClassifier(
    model=model,
    loss=loss,
    optimizer=optimizer,
    input_shape=(1, 28, 28),
    nb_classes=10,
    clip_values=(0.0, 1.0),
    preprocessing=(mean, std),
    preprocessing_defences=[SpatialSmoothing(channels_first=True, clip_values=(0.0, 1.0))],
    device_type="cpu",
)
```

Use estimator-level preprocessing when attacks should see the same pipeline as normal prediction/training. Keep `clip_values` in the raw input scale and choose `mean/std` accordingly.

## Preprocessing workflow

1. Confirm input dtype and range. Convert images or tabular arrays to floating point before standardisation or attacks.
2. Choose channel order once. For PyTorch image classifiers, prefer `NCHW` with `channels_first=True`; for NumPy preprocessing outside a PyTorch estimator, `NHWC` defaults are common.
3. Decide whether each defence applies at fit time, predict time, or both. Training augmentations (`GaussianAugmentation`, `Mixup`, `CutMix`, `Cutout`, `LabelSmoothing`) usually apply to fit; smoothing/compression often applies to prediction.
4. Verify one tiny batch by checking output shape, dtype, finite values, clipping, and labels.
5. Evaluate with adaptive or stronger attacks. Smoothing/compression can mask gradients; route robustness measurement to the evaluation/certification sub-skill.

## Adversarial training chooser

| Trainer | Import | Constructor | Fit method | Use when |
|---|---|---|---|---|
| Generic adversarial training | `from art.defences.trainer import AdversarialTrainer` | `AdversarialTrainer(classifier, attacks, ratio=0.5)` | `fit(x, y, batch_size=128, nb_epochs=20, **kwargs)` | You already have one or more evasion attack objects and want to mix clean/adversarial batches. |
| Madry PGD training | `from art.defences.trainer import AdversarialTrainerMadryPGD` | `AdversarialTrainerMadryPGD(classifier, nb_epochs=205, batch_size=128, eps=8, eps_step=2, max_iter=7, num_random_init=1)` | `fit(x, y, validation_data=None, batch_size=None, nb_epochs=None, **kwargs)` | You want a PGD-based training recipe with attack parameters owned by the trainer. Rescale defaults for `[0, 1]` inputs. |
| TRADES abstract/base | `from art.defences.trainer import AdversarialTrainerTRADES` | `AdversarialTrainerTRADES(classifier, attack, beta=6.0)` | `fit(x, y, validation_data=None, batch_size=128, nb_epochs=20, **kwargs)` | Backend-dispatched TRADES-style planning. Use the backend-specific class when available. |
| TRADES PyTorch | `from art.defences.trainer import AdversarialTrainerTRADESPyTorch` | `AdversarialTrainerTRADESPyTorch(classifier, attack, beta)` | `fit(x, y, validation_data=None, batch_size=128, nb_epochs=20, scheduler=None, **kwargs)` | PyTorch classifiers where the TRADES loss is required. |
| AWP/OAAT/FBF variants | `AdversarialTrainerAWPPyTorch`, `AdversarialTrainerOAATPyTorch`, `AdversarialTrainerFBFPyTorch` | backend-specific | backend-specific | Longer PyTorch research recipes; treat as reference planning unless the user explicitly requests the backend and budget. |

## Generic adversarial training recipe

```python
attack = ProjectedGradientDescent(
    estimator=classifier,
    eps=8 / 255,
    eps_step=2 / 255,
    max_iter=7,
    batch_size=64,
    verbose=False,
)
trainer = AdversarialTrainer(classifier, attacks=attack, ratio=0.5)
trainer.fit(x_train, y_train_onehot, batch_size=64, nb_epochs=5)
```

Checklist:

- `classifier` must support loss gradients.
- `attack` must be compatible with the classifier and input shape.
- `ratio` is the fraction of adversarial samples in each batch for generic training.
- `y_train` should be one-hot for classifier workflows that use one-hot labels.
- Use small `max_iter`, small batch size, and short epochs for CPU smoke checks; scale only after validating attack generation.

## Madry PGD recipe

```python
trainer = AdversarialTrainerMadryPGD(
    classifier,
    eps=8 / 255,
    eps_step=2 / 255,
    max_iter=7,
    num_random_init=1,
)
trainer.fit(x_train, y_train_onehot, batch_size=64, nb_epochs=5)
```

Important: constructor defaults `eps=8` and `eps_step=2` are pixel-scale numbers. If the estimator input is normalized to `[0, 1]`, explicitly pass fractions such as `8/255` and `2/255`.

## TRADES recipe

```python
attack = ProjectedGradientDescent(
    classifier,
    eps=8 / 255,
    eps_step=2 / 255,
    max_iter=7,
    verbose=False,
)
trainer = AdversarialTrainerTRADESPyTorch(classifier, attack=attack, beta=6.0)
trainer.fit(x_train, y_train_onehot, batch_size=64, nb_epochs=5)
```

Use TRADES when the user explicitly wants a clean/robustness trade-off objective. For PyTorch, ensure the classifier has an optimizer and can train on CPU or the requested device.

## Combining preprocessing and training

- Keep deterministic normalization (`StandardisationMeanStd` or estimator `preprocessing=(mean, std)`) in the estimator so attacks and training share the same view.
- Put stochastic or augmentation defences (`GaussianAugmentation`, `Mixup`, `CutMix`, `Cutout`) in training only unless the user explicitly wants prediction-time randomness.
- If prediction-time preprocessing is non-differentiable, test with attacks that account for the preprocessing or with black-box attacks; otherwise you may only measure gradient masking.
- Validate on a tiny synthetic or held-out batch before using large datasets.

## Minimal validation assertions

For any preprocessing/training workflow, assert:

- Input and output shapes are expected.
- Values are finite and inside `clip_values` after attack or clipping preprocessors.
- Labels are unchanged by sample-only preprocessors and transformed intentionally by label/mix augmentations.
- The attack used for adversarial training can generate adversarial samples independently before it is passed to a trainer.
- CPU workflows pass `device_type="cpu"` to PyTorch estimators unless GPU support is intentionally configured.
