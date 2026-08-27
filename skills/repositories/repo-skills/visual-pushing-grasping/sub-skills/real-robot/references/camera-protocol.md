# RealSense TCP RGB-D protocol

This is the fixed-frame contract implemented by the historical RealSense
server and `real/camera.py` client. The server listens on TCP port **50000**
by default and accepts a client on all local interfaces. The client defaults
to `127.0.0.1:50000`; change the host only after identifying the camera host
and checking its firewall/routing policy.

## Frame layout

The server transmits exactly one 1280x720 RGB-D frame per client ping. There
is no length header, magic number, checksum, version, or per-frame timestamp.
The historical validation dimensions are fixed at `W=1280` and `H=720`.
The byte stream is:

| Offset | Bytes | Interpretation |
|---:|---:|---|
| 0 | 36 | 9 raw 32-bit floats: row-major color intrinsics `K`, shape 3x3 |
| 36 | 4 | 1 raw 32-bit float: sensor depth scale |
| 40 | `W*H*2` = 1,843,200 | aligned depth, row-major `uint16`, shape HxW |
| 1,843,240 | `W*H*3` = 2,764,800 | RGB color, row-major `uint8`, shape HxWx3 |

The exact default payload is therefore **4,608,040 bytes** (`40 +
1280*720*5`). Component sizes are 36 + 4 + 1,843,200 + 2,764,800 bytes.
The depth and color frames are aligned to the color stream by the C++ server.
The color channel order is RGB8, not BGR.

The C++ implementation copies raw in-memory values into the socket buffer;
it does not add network-byte-order conversion. The deployed source target is
the usual little-endian x86 Ubuntu machine, so the bundled validator decodes
little-endian IEEE-754 floats. A different-endian server requires an explicit
adapter and must not be silently interpreted as valid.

## Request/response behavior

A client connects, sends any non-empty ping (the historical client sends
`asdf`), then reads until the complete fixed payload has arrived. A TCP
`recv()` is not a frame boundary: short reads are normal, and a robust client
must accumulate exact bytes. The server's single `send()` call can also be
short, so a client must not assume one response is complete. The server holds
a latest-frame buffer and sends it when pinged; if the client disconnects, it
returns to accept mode. The historical client keeps one socket open for
multiple `get_data()` calls.

Run the safe probe before any physical robot action. Let `<skill-root>` mean
the directory containing the root `SKILL.md`; the helper is bundled at the
explicit path below:

```bash
python <skill-root>/sub-skills/real-robot/scripts/capture_rgbd.py --help
python <skill-root>/sub-skills/real-robot/scripts/capture_rgbd.py \
  --host <CAMERA_HOST> --port 50000 --timeout 5
```

The default dimensions validate the historical 1280x720 contract. For a
synthetic or explicitly reviewed adapter check only, pass
`--compatibility-dimensions` together with non-default `--width` and
`--height`; the helper reports that this is not historical-protocol
validation. For a remote camera host, set `--host` to its confirmed address.
After the expected bytes, the helper performs a short bounded trailing-byte
probe: an observed extra byte rejects the response, peer close is reported as
an exact frame, and a probe timeout is reported as inconclusive rather than
silently accepted as exact. It reports dimensions, intrinsics, scale, payload
size, depth zero/finite/range statistics, and RGB range, but does not save or
display a frame.

## Units and downstream handoff

The wire depth values are sensor units. Multiply each `uint16` value by the
wire depth scale once to obtain metres; the separately reviewed application
then applies the fitted scalar from
`<CALIBRATION_OUTPUT_DIR>/camera_depth_scale.txt` once more. Do not apply the
wire scale in the validator's reported raw statistics and then mistake that
for calibration; report both raw values and the scale. The historical
`real/camera_depth_scale.txt` path is source evidence only.

The 3x3 intrinsics are pixel-coordinate values for the color image. The
camera pose and calibrated multiplier are separate deployment files. Hand
projection, pose composition, workspace clipping, and heightmap construction
to [perception-geometry](../../perception-geometry/SKILL.md).

## Boundary checks

Reject a frame if any of the following occurs: payload is shorter than
4,608,040 bytes, dimensions do not match the configured allocation, an
intrinsic is non-finite or `fx`/`fy` is zero, depth scale is non-finite or not
positive, the RGB/depth byte counts do not match, or the bounded probe observes
trailing bytes. A larger buffer is not a second frame: the protocol has no
framing. If the peer remains open and no byte arrives during the probe, exact
framing is inconclusive and must not be described as proven.
