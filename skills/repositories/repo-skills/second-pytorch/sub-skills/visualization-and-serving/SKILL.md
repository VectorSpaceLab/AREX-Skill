---
name: visualization-and-serving
description: "Guides the historical SECOND KITTI web viewer, its Flask API,
  browser configuration, visualization payloads, and guarded checkpoint
  inference routes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Visualization and serving

Use this route for requests such as **start the KITTI viewer web backend**,
**serve the browser UI**, **load point clouds or detections**, **configure
Flask/CORS**, **buildNet**, **run viewer inference**, or **use the PyQt viewer**.
The supported route here is the old repository's **web KITTI lidar viewer**;
the desktop Qt viewer is historical and deprecated.

## Safety and support boundary

- This is a source-distilled protocol, not a replacement server. A server is
  started only when the user explicitly asks for it, with user-owned paths and
  ports. No server, browser, GUI, dataset, or detector execution is part of
  skill verification.
- The checkout has no setup metadata. Do not assume `pip install -e .` works.
  First run the safe dependency probe:

  ```bash
  python sub-skills/visualization-and-serving/scripts/check_viewer_deps.py --json
  ```

  Missing components are reported without launching Flask. `--help` is also
  safe. A passing import probe does **not** prove detector compatibility.
- The historical model path uses legacy spconv/Numba APIs. Current spconv 2.x
  is not proven compatible: in the inspected environment the legacy
  `spconv.utils.VoxelGeneratorV2` and `non_max_suppression` symbols are absent.
  Do not claim that `buildNet` or inference works, even if CUDA and PyTorch
  import successfully. Route compatibility and checkpoints to
  [training-and-inference](../training-and-inference/SKILL.md).
- The backend binds to `127.0.0.1` and enables permissive Flask-CORS. CORS does
  not make a loopback server remotely reachable, and the API has no
  authentication. Keep it local or use an explicitly user-controlled secure
  tunnel; never expose arbitrary host paths or a public service by default.

## Web workflow

1. Prepare a local KITTI-style dataset and generated info pickle. Use
   [data-preparation](../data-preparation/SKILL.md) for layout and info
   validation; the browser sends filesystem paths to the **backend host**, not
   to the browser machine.
2. In a caller-managed environment where the `second` package and web
   dependencies are importable, start the backend only on request:

   ```bash
   python -m second.kittiviewer.backend.main main --port=<BACKEND_PORT>
   ```

   The source default is `16666`; the command is a long-running foreground
   service. Stop it with the terminal's normal interrupt. A safe import/help
   diagnostic is:

   ```bash
   python -m second.kittiviewer.backend.main --help
   ```

   If import fails before help, stop and use
   [troubleshooting](references/troubleshooting.md); do not silently substitute
   modern detector APIs.
3. Serve the supplied web frontend assets separately, from the directory that
   contains `index.html`, without exposing a broad parent directory:

   ```bash
   python -m http.server <FRONTEND_PORT> --directory <frontend-assets-directory>
   ```

   The README's example uses port `8000`. Open
   `http://127.0.0.1:<FRONTEND_PORT>/` in a browser and set the UI's **backend**
   field to `http://127.0.0.1:<BACKEND_PORT>` (the UI adds `http://` when a
   scheme is omitted). Verify browser developer tools show POSTs to the same
   backend origin and no CORS error.
4. Set **datasetClassName** to the registered class, normally
   `KittiDataset`, and set `rootPath` and `infoPath` to paths readable by the
   backend. Click **load**. Expect `status: normal` and an `image_indexes` list.
   Enter an index shown by that list in the bottom control and press Enter;
   previous/next only works after a successful load.
5. Optionally set **detPath** and click **loadDet**. The backend accepts either
   a pickled detection result file or a directory in the historical KITTI label
   format. Treat this as best-effort legacy state: the current endpoint stores
   `dt_annos`, but the point-cloud response does not consistently merge those
   annotations into its payload. Check the actual response before relying on
   `drawDet`.
6. For checkpoint inference, first complete **load**, then set
   **checkpointPath** and **configPath**, click **buildNet**, and only then
   click **inference**. This route is guarded and unverified for modern spconv;
   use [training-and-inference](../training-and-inference/SKILL.md) for
   checkpoint/config compatibility and [api-reference](references/api-reference.md)
   for exact request fields.

## Routes and handoffs

- Read [web-viewer.md](references/web-viewer.md) for the browser/backend state
  sequence, payload encodings, and visualization behavior.
- Read [api-reference.md](references/api-reference.md) before constructing a
  direct HTTP request or diagnosing a response shape.
- Read [troubleshooting.md](references/troubleshooting.md) for missing imports,
  CORS/URL mismatches, invalid info or detection inputs, API ordering errors,
  and legacy checkpoint failures.
- Route dataset directories, info generation, and dataset class registration
  to [data-preparation](../data-preparation/SKILL.md). Route box coordinate
  conventions and evaluation-format conversion to
  [geometry-and-evaluation](../geometry-and-evaluation/SKILL.md).

## Explicit non-goals

Do not copy, wrap, or launch the deprecated `viewer.py`, `glwidget.py`, or
`control_panel.py` desktop application. Those Qt/OpenGL modules require a
separate GUI stack and are retained only as deprecation evidence. Prefer the
web lidar path, and recommend a maintained successor such as OpenPCDet or
MMDetection3D for new work.
