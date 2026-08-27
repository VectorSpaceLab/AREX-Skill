# GIMP-ML architecture and route boundaries

Read this when a task crosses more than one GIMP-ML workflow or when a failure
could belong to the host, model, layer, or local service boundary.

## Two operating surfaces

**Legacy plug-ins** are Python-Fu procedures loaded by GIMP 2.10. The public
manual describes layer-oriented operations and the source entry points use
`gimpfu`, `register(...)`, GIMP PDB/pixel regions, and external `weights/` assets.
This surface is host-bound: a normal Python 3 interpreter cannot replace the
embedded GIMP Python-Fu runtime.

**The local service** is a Python 3 FastAPI application with a local HTTP
contract. The observed route set is `GET /status`, `POST /download_load_model`,
and `POST /run_inference`. The service can select text-to-image, text-edit,
text-extend, and outpaint tool objects. Its GIMP 2 bridge is a separate client
and does not establish GIMP 3 compatibility.

## Shared data boundary

Legacy plug-ins convert a GIMP drawable's pixel region into NumPy/OpenCV-like
arrays, enforce layer/image-size assumptions, run an operation, and add or
modify a result layer. The exact input contract belongs to the nearest
sub-skill. Do not use a service base64 payload as a substitute for a GIMP
pixel-region object.

The service carries raw `uint8` image bytes encoded as base64 plus a matching
`image_shape`; the payload validator under
`sub-skills/text-generation-service/scripts/` checks this contract without a
network. It is not a PNG/JPEG parser and must not be given encoded file bytes
unless the service client explicitly uses that format.

## Model and safety boundaries

Model checkpoint paths are evidence about the repository's expected external
asset layout, not bundled assets. Use the vision asset checker to report
missing files. Never let an updater download or overwrite them automatically.
OpenAI-backed operations require credentials, network, provider availability,
quota, and an intentional cost decision; none is implied by a configured field.

For GIMP work, preserve inputs and use a disposable or backed-up deployment for
host changes. For service work, keep the bind local, use an operator-provided
running loopback process, check `/status` first, and refuse to treat a status
response as inference validation.

## Cross-route selection

- Installation, missing menu, weights, permissions, port/lifecycle: `setup-and-host`.
- Pure array/K-means/palette/invert: `classical-image-ops`.
- Named restoration/depth/segmentation/super-resolution/interpolation: `vision-filters`.
- Mask, trimap, portrait-mask, or guided color: `guided-editing`.
- HTTP route, raw-image protocol, provider, or text pipeline: `text-generation-service`.

If a face edit first needs a face label map, use `guided-editing` and consult
`vision-filters` only for the separate segmentation prerequisite. If a service
client must be attached to a GIMP host, use both `text-generation-service` and
`setup-and-host`; do not merge their verification claims.
