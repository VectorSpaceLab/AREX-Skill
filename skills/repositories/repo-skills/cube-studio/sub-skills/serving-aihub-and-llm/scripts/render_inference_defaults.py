#!/usr/bin/env python3
"""Render distilled CubeStudio inference defaults.

This helper is standalone and safe:
- it does not import the original repository
- it does not start or query services
- it only prints a distilled framework summary
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

FRAMEWORKS: Dict[str, Dict[str, Any]] = {
    "serving": {
        "model_path": "user-defined",
        "command": "user-defined",
        "ports": "user-defined",
        "health": "user-defined",
        "metrics": "user-defined",
        "notes": "generic containerized service",
    },
    "ml-server": {
        "model_path": "sklearn/xgb artifact path",
        "command": "framework-specific model server",
        "ports": "custom",
        "health": "custom",
        "metrics": "custom",
        "notes": "supports classical ML artifact deployment",
    },
    "tfserving": {
        "model_path": "/mnt/.../saved_model",
        "command": "/usr/bin/tf_serving_entrypoint.sh --model_config_file=/config/models.config --monitoring_config_file=/config/monitoring.config --platform_config_file=/config/platform.config --rest_api_num_threads=300 --enable_batching=true",
        "ports": "8501",
        "health": "8501:/v1/models/$model_name/versions/$model_version/metadata",
        "metrics": "8501:/metrics",
        "env": ["TF_CPP_VMODULE=http_server=1", "TZ=Asia/Shanghai"],
    },
    "torch-server": {
        "model_path": "/mnt/.../$model_name.mar",
        "command": "cp $model_path /models/$model_name.mar && torchserve --start --model-store /models/ --models $model_name=$model_name.mar --ts-config=/config/config.properties --foreground",
        "ports": "8080,8081",
        "health": "8080:/ping",
        "metrics": "8082:/metrics",
        "configmap": "inference_address, management_address, metrics_address, CORS, queue, async logging",
    },
    "triton-server": {
        "model_path": "onnx:/mnt/.../model.onnx(model.plan,model.bin,model.savedmodel/,model.pt,model.dali)",
        "command": "tritonserver --model-repository=/models/ --strict-model-config=true --log-verbose=1",
        "ports": "8000,8002",
        "health": "8000:/v2/health/ready",
        "metrics": "8002:/metrics",
    },
}

SIDECARS = {
    "istio": "流量监控",
    "rate_limit": "限速(商业版)",
    "jwt": "token认证(商业版)",
    "monitor": "token统计(商业版)",
    "whitelist": "黑白名单(商业版)",
    "quotalimit": "额度限制(商业版)",
    "security": "内容安全(商业版)",
    "search": "联网查询(商业版)",
    "retry": "失败重试(商业版)",
    "desensitization": "数据脱敏(商业版)",
    "prompt": "提示词模板(商业版)",
    "value_map": "参数值映射(商业版)",
    "value_fixed": "参数值固定(商业版)",
}

SERVICE_TYPES = ["serving", "ml-server", "tfserving", "torch-server", "triton-server"]
TRAINING_SERVICE_TYPES = ["serving", "ml-server", "tfserving", "torch-server", "onnxruntime", "triton-server", "aihub"]


def render(framework: str | None) -> Dict[str, Any]:
    if framework:
        if framework not in FRAMEWORKS:
            raise KeyError(framework)
        frameworks = {framework: FRAMEWORKS[framework]}
    else:
        frameworks = FRAMEWORKS
    return {
        "service_types": SERVICE_TYPES,
        "training_service_types": TRAINING_SERVICE_TYPES,
        "frameworks": frameworks,
        "sidecars": SIDECARS,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", choices=sorted(FRAMEWORKS), help="Render one framework only.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    try:
        payload = render(args.framework)
    except KeyError as exc:
        print(f"unknown framework: {exc.args[0]}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("CubeStudio inference defaults")
        print(f"service_types: {', '.join(payload['service_types'])}")
        print(f"training_service_types: {', '.join(payload['training_service_types'])}")
        for name, info in payload["frameworks"].items():
            print(f"\n[{name}]")
            for key, value in info.items():
                if isinstance(value, list):
                    value = ", ".join(value)
                print(f"- {key}: {value}")
        print("\nsidecars:")
        for key, value in payload["sidecars"].items():
            print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
