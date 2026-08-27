# Server and Client Contracts (external native checkout)

These contracts describe native server/client entrypoints in a separate
checkout; they are not implementations in the generated skill. Set
`VLA_ADAPTER_REPO_ROOT` and run `cd <absolute-repo-root>` before any native
command. The bundled launch builder only prints commands, and the payload
validator only checks a synthetic payload without contacting a server.

VLA-Adapter includes two research server styles:

| Server style | Payload | Main use |
| --- | --- | --- |
| JSON + `json_numpy` | JSON body with numpy arrays encoded/decoded by `json_numpy` | Simple HTTP action serving and debugging. |
| MsgPack + `msgpack_numpy` | `application/msgpack` request/response | ALOHA fake and real clients; lower overhead for image/proprio arrays. |

Both expose an `/act` endpoint and load a policy checkpoint on CUDA. The server
must know model flags such as `model_family`, `use_l1_regression`,
`use_minivlm`, `use_film`, `num_images_in_input`, `use_proprio`, quantization
flags, and `unnorm_key` behavior.

## MsgPack request schema

The ALOHA MsgPack server/client contract uses these keys:

```text
full_image: uint8 image array, resized for policy
left_wrist_image: uint8 image array, resized for policy
right_wrist_image: uint8 image array, resized for policy
state: float array, 14 values for ALOHA bimanual qpos
instruction: natural-language task label
unnorm_key: dataset statistics key used to denormalize predicted actions
```

The server returns a mapping containing `actions`, usually a list/array of
action chunks. ALOHA defaults to 25 open-loop actions per query; LIBERO/CALVIN
use 8-action chunks in the constants table.

## JSON request schema

The JSON server expects an observation with an `instruction` and image/proprio
fields accepted by the shared action helper. It supports a double-encoded mode
where payloads contain only an `encoded` JSON string for clients that cannot
transport numpy objects directly.

## Launch review

Use the skill-local `scripts/build_aloha_launch.py` by absolute skill path with
`--repo-root "$VLA_ADAPTER_REPO_ROOT"` to print commands for:

- `server`: launch the MsgPack server with checkpoint, port, model family, and
  CUDA device.
- `fake-client`: query the server with deterministic fake images and 14D qpos;
  no ROS is required by the native fake client.
- `real-client`: query the server from a ROS environment and publish bimanual
  joint commands.

The builder does not execute any command. Inspect every path, port, task label,
and unnormalization key before running in the external checkout.

## Synthetic validation

Use the skill-local `scripts/validate_msgpack_payload.py` by absolute skill
path to generate or validate payload shape before connecting to a server. This
catches missing keys, image dtype/shape errors, and wrong ALOHA state
dimensions early; it is not a server/client probe.
