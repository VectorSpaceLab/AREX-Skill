#!/usr/bin/env python3
"""Render safe Xinference CLI command templates.

This script prints command templates only. It never starts a server, launches a
model, downloads anything, or touches the network.
"""

from __future__ import annotations

import argparse
from textwrap import dedent

TEMPLATE = dedent(
    """
    # Xinference command templates

    > Safety: these are templates only. They do not start services or launch models.
    > Real launches may download model weights and per-model dependencies.
    > Choose the right backend and hardware before launch.

    ## Local cluster

    ```bash
    xinference-local --host <LOCAL_BIND_HOST> --port <SERVICE_PORT> --log-level INFO
    ```

    ## Distributed cluster

    ```bash
    xinference-supervisor -H <SUPERVISOR_BIND_HOST> -p <SERVICE_PORT> --supervisor-port <SUPERVISOR_PORT>
    xinference-worker -e http://<SUPERVISOR_HOST>:<SERVICE_PORT> -H <WORKER_BIND_HOST> --worker-port <WORKER_PORT> --metrics-exporter-host <METRICS_HOST> --metrics-exporter-port <METRICS_PORT>
    ```

    ## Model launch

    ```bash
    xinference launch -e <ENDPOINT> -n <MODEL_NAME> -t LLM -en <MODEL_ENGINE> -u <MODEL_UID> -s <SIZE_IN_BILLIONS> -f <MODEL_FORMAT> -q <QUANTIZATION> -r <REPLICA> --n-worker <N_WORKER> --n-gpu <N_GPU> --worker-ip <WORKER_IP:PORT> --gpu-idx <GPU_IDX,COMMA_SEPARATED> --trust-remote-code <BOOL> -ak <API_KEY> -mp <MODEL_PATH> --enable-thinking --enable-virtual-env --virtual-env-package <PACKAGE_SPEC> --env KEY VALUE
    # swap --enable-virtual-env for --disable-virtual-env when you want to override the default
    # optional extras: -lm <LORA_NAME> <LORA_PATH>...  -qc <KEY> <VALUE>...  -ld <KEY> <VALUE>...  -fd <KEY> <VALUE>...
    # legacy compatibility alias: --model_path <MODEL_PATH>
    ```

    ## Model lifecycle

    ```bash
    xinference list -e <ENDPOINT> -ak <API_KEY>
    xinference registrations -e <ENDPOINT> --model-type LLM -ak <API_KEY>
    xinference register -e <ENDPOINT> --model-type LLM --file <MODEL_CONFIG_FILE> --worker-ip <WORKER_IP:PORT> --persist -ak <API_KEY>
    xinference unregister -e <ENDPOINT> --model-type LLM --model-name <MODEL_NAME> -ak <API_KEY>
    xinference cached -e <ENDPOINT> --model_name <MODEL_NAME> --worker-ip <WORKER_IP:PORT> -ak <API_KEY>
    xinference remove-cache -e <ENDPOINT> --model_version <MODEL_VERSION> --worker-ip <WORKER_IP:PORT> -ak <API_KEY>
    xinference terminate -e <ENDPOINT> --model-uid <MODEL_UID> -ak <API_KEY>
    xinference engine -e <ENDPOINT> -n <MODEL_NAME> --model-engine <MODEL_ENGINE> --model-format <MODEL_FORMAT> --model-size-in-billions <SIZE_IN_BILLIONS> --quantization <QUANTIZATION> -ak <API_KEY>
    xinference cal-model-mem -n <MODEL_NAME> --size-in-billions <SIZE_IN_BILLIONS> --model-format <MODEL_FORMAT> --quantization <QUANTIZATION> --context-length <CONTEXT_LENGTH>
    xinference vllm-models -e <ENDPOINT> -ak <API_KEY>
    xinference login -e <ENDPOINT> --username <USERNAME> --password <PASSWORD>
    xinference stop-cluster -e <ENDPOINT> -ak <API_KEY>
    ```

    ## Reminders

    - `launch` needs `--model-engine` for LLMs.
    - `--endpoint` targets the cluster service endpoint.
    - `--worker-ip` must be the full registered `IP:port`.
    - `--gpu-idx` is comma-separated integers.
    - `--n-gpu none` disables GPU binding; `auto` lets Xinference choose.
    - Use `--enable-virtual-env` or `--disable-virtual-env`, not both.
    - `remove-cache` and `stop-cluster` are destructive; review them carefully before copying.
    """
).strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render safe Xinference CLI command templates."
    )
    parser.parse_args()
    print(TEMPLATE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
