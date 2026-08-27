# Messaging and Params Reference

## Verified APIs

```text
messaging.new_message(service: str | None, size: int | None = None, **kwargs)
messaging.pub_sock(endpoint: str)
messaging.sub_sock(endpoint: str, poller=None, addr='127.0.0.1', conflate=False, timeout=None)
messaging.drain_sock(sock, wait_for_one=False)
messaging.recv_sock(sock, wait=False)
messaging.SubMaster(services, poll=None, ignore_alive=None, ignore_avg_freq=None, ignore_valid=None, addr='127.0.0.1', frequency=None)
messaging.PubMaster(services)
Params.get(self, key, block=False, return_default=False)
Params.put(self, key, dat, block=False)
Params.put_bool(self, key, val, block=False)
Params.get_bool(self, key, block=False)
Params.remove(self, key)
Params.clear_all(self, tx_flag=<ParamKeyFlag.ALL>)
Params.all_keys(self)
```

## Messaging notes

- `new_message` returns a Cap'n Proto builder whose `.which()` should match the requested service.
- `SubMaster` keeps dictionaries for `updated`, `seen`, `alive`, `valid`, `recv_time`, `recv_frame`, and `logMonoTime` keyed by service name.
- `SubMaster` conflates by default; later messages replace earlier queued values for a service.
- `PubMaster` accepts either builders or raw bytes.
- `drain_sock` returns a list of decoded messages; `recv_sock` returns one message or `None` on timeout.

## Params notes

- Keys are typed and some keys have defaults; `get(..., return_default=True)` can return a repo-defined default when no explicit value is present.
- `put`/`put_bool` and `clear_all` mutate persistent state. Avoid them in ordinary analysis unless the task is explicitly about device state.
- Unknown keys raise `UnknownKeyName`.
- The filesystem backing for Params depends on `Paths` and the host/device environment.

## Native prerequisites

Many messaging/runtime imports require built native outputs:

- `openpilot/common/libparams_c.so`
- `msgq_repo/msgq/ipc_pyx.so`
- `msgq_repo/msgq/visionipc/visionipc_pyx.so`

If those are absent, build them before expecting `openpilot.cereal.messaging` or `openpilot.common.params` imports to succeed.
