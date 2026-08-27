# U-2-Net Model Weights

## Policy

The generated skill does not bundle pretrained weights and does not download them automatically. Downloads from Google Drive, Baidu Pan, or other mirrors are network-affecting and should be run only after user approval.

## Weight map

| File | Workflow | Architecture | Owning sub-skill |
| --- | --- | --- | --- |
| `u2net.pth` | Full salient object detection | `U2NET(3,1)` | `salient-object-inference` |
| `u2netp.pth` | Lightweight salient object detection | `U2NETP(3,1)` | `salient-object-inference` |
| `u2net_human_seg.pth` | Human/person segmentation | `U2NET(3,1)` | `salient-object-inference` |
| `u2net_portrait.pth` | Portrait generation/compositing | `U2NET(3,1)` | `portrait-workflows` |

## Placement

Bundled helpers accept explicit `--weights PATH` values, so users may keep weights in any approved local directory. Do not recreate repository-specific directories unless another non-skill tool explicitly requires that layout.

## Verification limitation

If weights are absent, final verification should run architecture/data/helper smoke checks and record pretrained native inference as blocked by missing external artifacts, not as pass or fail.
