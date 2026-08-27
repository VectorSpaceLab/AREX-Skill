# Model Overview

## Purpose

Read this when the user asks which OFA model family to load or which hub entry
matches a particular inference workflow.

## Supernet families

| Helper | Design space | Notes |
| --- | --- | --- |
| `ofa_net('ofa_resnet50', pretrained=...)` | ResNet50 design space | Returns an OFA-ResNet50 supernet with depth, width, and expansion choices. |
| `ofa_net('ofa_mbv3_d234_e346_k357_w1.0', pretrained=...)` | MobileNetV3 | Fixed width 1.0 with depth, expansion, and kernel choices. |
| `ofa_net('ofa_mbv3_d234_e346_k357_w1.2', pretrained=...)` | MobileNetV3 | Wider variant intended for higher-resolution settings. |
| `ofa_net('ofa_proxyless_d234_e346_k357_w1.3', pretrained=...)` | ProxylessNAS | Wider ProxylessNAS-style OFA supernet. |

## Specialized families

The specialized helper resolves public ids in families such as:

- `flops@...`
- `resnet50D_MAC@...`
- `pixel1_lat@...`
- `pixel2_lat@...`
- `note10_lat@...`
- `note8_lat@...`
- `s7edge_lat@...`
- `LG-G8_lat@...`
- `1080ti_gpu64@...`
- `v100_gpu64@...`
- `tx2_gpu16@...`
- `cpu_lat@...`

The helper returns `(net, image_size)`, so the evaluation resolution is part of the model contract.

## Hub shortcuts

The repo's `hubconf.py` exposes ready-made partials such as:

- `ofa_supernet_resnet50`
- `ofa_supernet_mbv3_w10`
- `ofa_supernet_mbv3_w12`
- `ofa_supernet_proxyless`
- `resnet50D_MAC_4_1B`
- `resnet50D_MAC_3_7B`
- `resnet50D_MAC_3_0B`
- `resnet50D_MAC_2_4B`
- `resnet50D_MAC_1_8B`
- `resnet50D_MAC_1_2B`
- `resnet50D_MAC_0_9B`
- `resnet50D_MAC_0_6B`

These partials are convenient for `torch.hub`-style loading and for routing from a simple model id.
