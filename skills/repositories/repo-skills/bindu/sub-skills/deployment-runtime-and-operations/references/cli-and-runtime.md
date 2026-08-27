# CLI and Runtime

## CLI

- `bindu serve --grpc [--grpc-port 3774]`: start the core gRPC server for SDK registration.
- `bindu serve --script PATH`: execute a Python script that calls `bindufy()`.
- `bindu deploy SCRIPT --runtime=boxd [options]`: package and deploy an agent script to a boxd microVM.
- `bindu logs AGENT [--no-follow]`: stream in-VM agent logs.
- `bindu shell AGENT`: open an interactive shell on the VM.

## Runtime config

`RuntimeConfig` supports `provider="in-process"` and `provider="boxd"`. Boxd options include `image`, `vcpu`, `memory`, `disk`, `auto_suspend`, `on_exit`, `bindu_version`, and `env`.

`on_exit` choices: `suspend`, `destroy`, `detach`. `auto_suspend` defaults to `0` because Bindu agents often have background tasks or streaming calls.

## Boxd modes

- A2/default: ship source, install dependencies in the VM, run the script.
- A1/custom image: pass `--image`; VM starts from image command and source is not shipped.

Use `--bindu-version=local` only when intentionally shipping a patched Bindu source into the VM.
