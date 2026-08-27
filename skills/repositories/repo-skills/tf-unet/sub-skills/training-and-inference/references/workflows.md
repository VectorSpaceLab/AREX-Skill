# Training and inference workflows

## 1. Tiny smoke workflow

Use the bundled smoke helper when you only need to confirm that the model graph, save/restore path, and prediction path are alive.

```bash
python scripts/smoke_train_restore.py
```

That helper uses a tiny synthetic dataset, a shallow graph, and temporary directories so it is safe for routine inspection.

## 2. Standard toy segmentation workflow

A normal toy workflow looks like this:

```python
from tf_unet import unet, util
from tf_unet.image_gen import GrayScaleDataProvider

data = GrayScaleDataProvider(nx=572, ny=572, cnt=20)
net = unet.Unet(channels=data.channels, n_class=data.n_class, layers=3, features_root=16)
trainer = unet.Trainer(net, optimizer="momentum", opt_kwargs=dict(momentum=0.2))
path = trainer.train(data, output_path, training_iters=32, epochs=5, dropout=0.75)

x_test, y_test = data(4)
prediction = net.predict(path, x_test)
score = unet.error_rate(prediction, util.crop_to_shape(y_test, prediction.shape))
```

Key points:

- The default toy generator expects a large enough image size for the chosen border and circle radius.
- Crop the label before comparing with the prediction.
- Use `create_training_path` when you want a fresh run directory.

## 3. Save/restore workflow

When you need to continue a run or inspect a checkpoint:

1. Train or initialize a model.
2. Save the checkpoint base path such as `.../model.ckpt`.
3. Recreate the same graph configuration.
4. Call `predict(...)` with the saved checkpoint base path.

Do not change `layers`, `features_root`, or `n_class` between save and restore unless you intend to break compatibility.

## 4. Loss and optimizer selection

- `optimizer="momentum"` is the default legacy path.
- `optimizer="adam"` is useful for simpler inspection smokes.
- `cost="cross_entropy"` is the default segmentation loss.
- `cost="dice_coefficient"` is the alternative segmentation loss.
- `class_weights` and `regularizer` are both passed through `cost_kwargs`.

## 5. Visualization workflow

Use `util.combine_img_prediction(...)` and `util.save_image(...)` when you want a quick visual check of input, ground truth, and prediction. Use `util.plot_prediction(...)` when you want an interactive matplotlib view instead of a JPEG snapshot.
