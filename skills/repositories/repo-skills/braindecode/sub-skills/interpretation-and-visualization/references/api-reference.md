# Interpretation and visualization API reference

Captum-backed wrappers include `saliency`, `input_x_gradient`,
`integrated_gradients`, `layer_grad_cam`, `guided_backprop`, `deconvolution`,
`deep_lift`, and `lrp`. They accept a model, an input tensor shaped
`(batch, channels, time)`, and target indices; integrated gradients and DeepLIFT
also accept a baseline. Results retain input-like axes except layer methods,
which may be interpolated or squeezed.

`amplitude_gradients(model, inputs)` and its per-trial variant expose frequency
sensitivity. Interpret bins using the actual sampling rate and validate a known
small convolution before applying it to a trained model.

Topomaps require channel names/positions and a montage consistent with model
input order. Metric/confusion plotting functions consume NumPy-like targets and
predictions; validate class labels and lengths before plotting.
