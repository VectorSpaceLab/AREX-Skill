# Host compatibility and deployment contracts

Use this reference to classify a host before choosing installation. “Compatible” means that the stated prerequisites are present; it does not mean that a model result has been reproduced.

## Compatibility matrix

| Layer | Historical GIMP plug-ins | Newer installed local service | What can be claimed now |
|---|---|---|---|
| Host application | GIMP 2.10 with Python-Fu/PDB | An installed GIMP-ML application or operator-managed local service; no GIMP process is required for HTTP liveness | GIMP is unavailable on the inspected host; no menu/PDB claim |
| Python | Embedded/compatible Python 2.7 and `gimpfu` | Python 3 service-core environment | The inspected Python 3.11 environment imported the FastAPI application and route declarations; it cannot load legacy `gimpfu` plug-ins |
| Registration | `register(...)`, menu metadata, and `main()` | FastAPI route declarations | Static registrations and route declarations were inspected; no host load or live bind was claimed |
| Model assets | External `weights/<model>/...` files | Provider/model-dependent assets | No weights are assumed or downloaded |
| OpenAI/provider | Legacy plug-ins do not establish provider access | Provider credentials and authorization are deployment inputs | No provider request is allowed by this guide |
| GPU | Legacy plug-ins select CPU/GPU flags and load local checkpoints | Service liveness does not prove ML device availability | CUDA was visible on the host, but a tiny allocation hit CUDA OOM |
| Platform launcher dependencies | GIMP/Python-Fu host integration | PyQt6, PyQt6-WebEngine, and pywin32 may be launcher-only/platform-specific | Those launcher packages were not installed or verified; do not claim an installed launcher is usable from service-core evidence |
| GIMP generation | GIMP 2.10 only in cited historical evidence | HTTP service is not a GIMP-generation contract | Do not promise GIMP 3 compatibility |

## Evidence-derived legacy contract

Historical installation evidence describes computer-vision plug-ins such as depth, segmentation, matting, super-resolution, denoising, coloring, and image processing. It expects an external `weights/` tree, a compatible GIMP 2.10/Python-Fu host, and a readable/executable plug-in deployment. A static registration scan is only an entry-point hint, not runtime proof.

## Expected weight layout

The historical plug-ins reference these relative model directories/files. Presence is a prerequisite only; this guide does not verify file integrity or download them.

| Model directory | Referenced file(s) |
|---|---|
| `weights/deepmatting` | `stage1_sad_57.1.pth` |
| `weights/MiDaS` | `model.pt` |
| `weights/colorize` | `caffemodel.pth` |
| `weights/super_resolution` | `model_srresnet.pth` |
| `weights/faceparse` | `79999_iter.pth` |
| `weights/deblur` | `mymodel.pth`, `best_fpn.h5` |
| `weights/deeplabv3` | `deeplabv3+model.pt` |
| `weights/facegen/label2face_512p` | `latest_net_G.pth` |
| `weights/deepdehaze` | `dehazer.pth` |
| `weights/deepdenoise` | `est_net.pth`, `net.pth` |
| `weights/enlightening` | `200_net_G_A.pth` |
| `weights/interpolateframes` | `contextnet.pkl`, `flownet.pkl`, `unet.pkl` |
| `weights/inpainting` | `model_places2.pth`, `refinement.pth` |

A directory can exist while an individual file is absent, unreadable, truncated, or incompatible. Use the bundled layout checker for presence/readability only. Never describe a model as “installed” from directory existence alone.

## Registration and service boundary

Historical Python-Fu entries call `register()` with a procedure identifier, display label, parameter definitions, and a menu. The newer GIMP-2-oriented bridge uses procedure names and a local service port. These are static patterns used as evidence; they do not establish GIMP 3 support.

The inspected FastAPI application declared:

| Method | Route | Safe setup boundary |
|---|---|---|
| GET | `/status` | Liveness only; returns process/system status fields |
| POST | `/download_load_model` | Model/provider initialization; do not call during host setup |
| POST | `/run_inference` | Model execution; requires real data/model/provider setup and is outside safe setup |

Use the bundled status helper only after an installed application/operator confirms an already running loopback service and supplies its active port. A successful response establishes HTTP liveness, not weights, provider credentials, GPU capacity, or inference correctness.

## Host verdict procedure

1. **Legacy candidate:** report `eligible`, `blocked`, or `unknown` for each of GIMP 2.10, Python 2.7/Python-Fu, plug-in path, legacy environment, and required weight files. Any missing host/runtime item blocks a menu/PDB claim.
2. **Service candidate:** report whether a supported installed launcher/operator procedure is available, whether an active loopback port was supplied, and whether `scripts/check_service_status.py --port <active-port>` succeeded. Without the launcher/procedure or port, service startup is deployment-specific and blocked.
3. **Resource verdict:** keep CUDA and memory as advisory. The checked machine exposed CUDA but could not allocate a tiny device buffer, so do not recommend GPU inference without a fresh resource check.
4. **Publication verdict:** only report a working mode after the corresponding host-level check has been performed. Static evidence alone is `static-only`.

## Explicit exclusions

Do not install or revive Python 2 merely to make a modern host appear compatible; do not treat GIMP 3 as a drop-in; do not run an updater/downloader; do not paste a provider secret into a configuration file; do not claim that a route response means an image was generated; and do not use a public network bind for this local service without a separately reviewed security design.

## Evidence and provenance — not runtime instructions

Historical source artifacts such as `service.py`, `config.json`, `GIMPML.py`, and the GIMP-2 bridge files established the route and launcher observations above. They remain provenance only. Do not locate, open, run, import, or adapt those artifacts while following this skill.
