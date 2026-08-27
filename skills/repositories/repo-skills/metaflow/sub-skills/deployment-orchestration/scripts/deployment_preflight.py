#!/usr/bin/env python3
"""Read-only Metaflow deployment preflight.

Example:
  python deployment_preflight.py --json
"""
import argparse
import importlib.util
import json
import os

OPTIONAL_MODULES = ["boto3", "kubernetes", "airflow"]
CONFIG_KEYS = [
    "METAFLOW_DEFAULT_DATASTORE",
    "METAFLOW_DATASTORE_SYSROOT_S3",
    "METAFLOW_SERVICE_URL",
    "METAFLOW_BATCH_JOB_QUEUE",
    "METAFLOW_ECS_S3_ACCESS_IAM_ROLE",
    "METAFLOW_KUBERNETES_NAMESPACE",
    "METAFLOW_ARGO_EVENTS_EVENT_BUS",
    "METAFLOW_SFN_STATE_MACHINE_PREFIX",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Report optional deployment modules and non-secret Metaflow config presence.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = {
        "optional_modules": {name: importlib.util.find_spec(name) is not None for name in OPTIONAL_MODULES},
        "config_present": {key: bool(os.environ.get(key)) for key in CONFIG_KEYS},
        "warning": "This preflight does not contact cloud APIs or prove credentials/services are valid.",
    }
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
