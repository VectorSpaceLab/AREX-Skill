# API Reference

## Purpose

Read this for the verified public inference APIs and the main subnet methods.

## Constructors and loaders

| API | Signature | Returns | Notes |
| --- | --- | --- | --- |
| `ofa.model_zoo.ofa_net` | `ofa_net(net_id, pretrained=True)` | OFA supernet | Supported ids include `ofa_resnet50`, `ofa_mbv3_d234_e346_k357_w1.0`, `ofa_mbv3_d234_e346_k357_w1.2`, and `ofa_proxyless_d234_e346_k357_w1.3`. |
| `ofa.model_zoo.ofa_specialized` | `ofa_specialized(net_id: str, pretrained=True)` | `(net, image_size)` | Special ids encode FLOPs, latency, or device families. The returned `image_size` is part of the contract. |

## Supernet methods

| Class | Method | Purpose |
| --- | --- | --- |
| `OFAMobileNetV3` | `set_active_subnet(ks=None, e=None, d=None, **kwargs)` | Fix kernel-size, expansion, and depth choices. |
| `OFAMobileNetV3` | `sample_active_subnet()` | Randomly sample a valid active subnet. |
| `OFAMobileNetV3` | `get_active_subnet(preserve_weight=True)` | Materialize the active subnet as a plain network. |
| `OFAMobileNetV3` | `get_active_net_config()` | Export the active configuration as a serializable dict. |
| `OFAProxylessNASNets` | `set_active_subnet(ks=None, e=None, d=None, **kwargs)` | Fix ProxylessNAS subnet choices. |
| `OFAProxylessNASNets` | `sample_active_subnet()` | Sample a valid ProxylessNAS subnet. |
| `OFAResNets` | `set_active_subnet(d=None, e=None, w=None, **kwargs)` | Fix depth, expansion, and width choices. |
| `OFAResNets` | `sample_active_subnet()` | Sample a valid ResNet-family subnet. |

## Behavioral notes

- `get_active_subnet(preserve_weight=True)` is the easiest way to turn a sampled
  subnet into a stand-alone model for smoke checks or downstream export.
- `sample_active_subnet()` also mutates the model's runtime state, so call it only
  when you intend to evaluate that exact sample.
- `ofa_specialized(...)` loads a model and its image-size hint; do not hard-code
  the evaluation resolution.
