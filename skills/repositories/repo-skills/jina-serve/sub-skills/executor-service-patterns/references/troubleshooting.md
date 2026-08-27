# Executor and Deployment Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `TypeError` says `__init__` signature is wrong | Executor constructor omitted `**kwargs`. | Add `**kwargs` and call `super().__init__(**kwargs)`. |
| Executor class cannot be imported | `py_modules` missing/wrong, class is nested, or module path is not importable. | Put class at top level in `executor.py`; include `py_modules: [executor.py]`; use `extra_search_paths` if needed. |
| Deployment closes after an exception inside `with dep:` | Context manager exits on exception. | Wrap request code in `try/except` or serve with `dep.block()` in a server process. |
| Spawn/fork errors on Windows/macOS/CUDA | Startup code is not under `if __name__ == '__main__':`, or CUDA was initialized before fork. | Use top-level classes, a `main()` function, `if __name__ == '__main__':`, and `JINA_MP_START_METHOD=spawn` for CUDA. |
| Endpoint does not receive requests | Wrong `on=` endpoint or overwritten `uses_requests` mapping. | Print/inspect `self.requests`, check `@requests(on=...)`, and call the exact endpoint. |
| Dynamic batching changes output order or size | Method does not return one output per input or batch semantics are wrong. | Ensure batch output aligns with input order and size; test with small DocLists first. |
| GPU Executor fails with missing torch/diffusers/tensorflow | Jina does not install model framework dependencies. | Add model framework wheels to the service requirements/container and verify device availability separately. |
| Stateful replicas diverge | Non-deterministic state updates or missing snapshot/restore/write semantics. | Use deterministic writes, implement snapshot/restore where needed, and avoid stateful replicas if not required. |
