#!/usr/bin/env python3
"""Tiny CPU-only RayOrch smoke for the rayorch-acceleration sub-skill."""
from __future__ import annotations


def _check_optional_dependencies() -> list[tuple[str, Exception]]:
    missing: list[tuple[str, Exception]] = []
    try:
        import ray  # noqa: F401
    except Exception as exc:  # pragma: no cover - import guard
        missing.append(("ray", exc))
    try:
        import rayorch  # noqa: F401
    except Exception as exc:  # pragma: no cover - import guard
        missing.append(("rayorch", exc))
    return missing


def main() -> int:
    missing = _check_optional_dependencies()
    if missing:
        print("RayOrch CPU smoke skipped: optional dependency not available.")
        for name, exc in missing:
            print(f"  - {name}: {exc}")
        print("Install the Ray/RayOrch backend in this environment, then rerun.")
        return 0

    try:
        import ray
        import pandas as pd
        from dataflow.core.operator import OperatorABC
        from dataflow.rayorch import RayAcceleratedOperator
        from dataflow.rayorch.memory_storage import InMemoryStorage
    except Exception as exc:
        print("RayOrch CPU smoke could not start because a required runtime import failed.")
        print(f"  - {exc.__class__.__name__}: {exc}")
        return 1

    class TinyDoubleOp(OperatorABC):
        def run(self, storage, input_key: str = "value", output_key: str = "doubled") -> None:
            df = storage.read("dataframe").copy()
            df[output_key] = df[input_key] * 2
            storage.write(df)

    ray_was_started = False
    if not ray.is_initialized():
        ray.init(
            ignore_reinit_error=True,
            num_cpus=2,
            include_dashboard=False,
            log_to_driver=False,
        )
        ray_was_started = True

    op = None
    try:
        storage = InMemoryStorage(pd.DataFrame({"value": [1, 2, 3, 4]}))
        op = RayAcceleratedOperator(
            TinyDoubleOp,
            replicas=2,
            num_gpus_per_replica=0.0,
        ).op_cls_init()
        op.run(storage=storage.step(), input_key="value", output_key="doubled")

        result = storage.result
        expected = [2, 4, 6, 8]
        actual = result["doubled"].tolist()
        if result["value"].tolist() != [1, 2, 3, 4]:
            raise AssertionError("Input row order changed during CPU smoke.")
        if actual != expected:
            raise AssertionError(f"Unexpected doubled values: {actual!r}")
        if getattr(op, "_module", None) is None:
            raise AssertionError("Ray actors were not created on first run.")

        print("RayOrch CPU smoke passed.")
        print("  rows=4 replicas=2 num_gpus_per_replica=0.0")
        print(f"  output={actual}")
        return 0
    except Exception as exc:
        print("RayOrch CPU smoke failed.")
        print(f"  - {exc.__class__.__name__}: {exc}")
        return 1
    finally:
        if op is not None:
            try:
                op.shutdown()
            except Exception as exc:
                print(f"Cleanup warning: {exc.__class__.__name__}: {exc}")
            else:
                if getattr(op, "_module", "sentinel") is not None:
                    print("Cleanup warning: actor module still attached after shutdown().")
        if ray_was_started and ray.is_initialized():
            ray.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
