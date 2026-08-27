# Troubleshooting

## No training data
**Symptom:** training stops immediately with a message that no training data was provided.

**Likely cause:** the training list resolves to an empty dataset.

**Fix:** provide a non-empty training list before starting the run.

## No validation samples
**Symptom:** training runs but no preview images are saved.

**Likely cause:** `SAMPLE_INTERVAL` is `0`, the validation list is empty, or the validation iterator has no items to draw.

**Fix:** set `SAMPLE_INTERVAL` to a positive value and provide a non-empty validation list.

## CUDA unavailable
**Symptom:** the run falls back to CPU or becomes impractically slow.

**Likely cause:** no CUDA-capable device is visible, or the environment does not have a CUDA build.

**Fix:** use a CUDA-enabled environment for real training. CPU mode is acceptable only for tiny smoke tests; reduce `BATCH_SIZE` and `INPUT_SIZE` if you need a short inspection run.

## Legacy dependency or API deprecation
**Symptom:** imports fail or image utilities disappear in a modern stack.

**Likely cause:** the code path depends on legacy APIs such as `scipy.misc.imread`, `scipy.misc.imresize`, `skimage.measure.compare_psnr`, `skimage.measure.compare_ssim`, `yaml.load` without a loader argument, or `torchvision.models.vgg19(pretrained=True)`.

**Fix:** pin a compatible legacy stack or add compatibility shims. Do not upgrade one dependency in isolation and expect the whole pipeline to keep working.

## Missing VGG or pretrained weight downloads
**Symptom:** perceptual/style losses fail to initialize, block on first run, or complain about missing weights.

**Likely cause:** `torchvision` cannot fetch pretrained VGG19 weights.

**Fix:** pre-cache the weights in a networked environment, then reuse the cache in offline runs.

## NaN, inf, or exploding losses
**Symptom:** losses become NaN, jump wildly, or stop making sense.

**Likely cause:** image tensors are not scaled into `[0, 1]`, masks are empty or malformed, loss weights are too aggressive, or the chosen `GAN_LOSS` does not match the intended stage.

**Fix:** verify input scaling, keep masks binary and non-empty, start from the bundled template defaults, and confirm that the stage selection matches the intended behavior.

## Resume looks fresh
**Symptom:** a run starts from iteration 0 even though checkpoints exist.

**Likely cause:** the generator checkpoint is missing or the wrong checkpoint family is in the checkpoint directory. The discriminator checkpoint is optional and is only loaded in training mode.

**Fix:** confirm the expected `*_gen.pth` files exist for the selected `MODEL`. If only `*_dis.pth` is missing, the run should still resume generator state.

## Configuration surprises
**Symptom:** the run behaves differently from the written plan.

**Likely cause:** `MODE` was changed when `MODEL` should have been changed, or vice versa.

**Fix:** remember that `MODE` selects train/test/eval, while `MODEL` selects edge, inpaint, edge-inpaint, or joint training.

**Note:** the current `MODEL = 3` implementation always uses predicted edges from the edge model.
