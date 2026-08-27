# Synthesis and serving CLI

## Batch evaluation

Use the bundled synthesis command builder in `eval` mode with the required
checkpoint and optional hparams. Its printed command mirrors the repository's
batch-evaluation entry point; review it before intentional execution.

The checkpoint argument is required. Hparams are parsed before loading the
model. Outputs are written beside the checkpoint in an `eval...` directory/base
pattern.

## Browser demo

Use the bundled synthesis command builder in `server` mode with the required
checkpoint, optional port, and optional hparams. Its printed command mirrors
the repository's demo-server entry point; it never opens a listener.

`--port` defaults to 9000. The server loads the checkpoint before serving and
prints the selected hparams. A missing checkpoint therefore fails at startup,
not on the first browser request.

Use `scripts/build_synthesis_command.py --mode eval|server` for a dry-run
command. Do not put credentials in hparams or expose a demo server to an
untrusted network without a real authentication/reverse-proxy design.
