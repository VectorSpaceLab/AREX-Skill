from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass
class Result:
    path: str
    status: int
    body: object


def _request(base_url: str, path: str, method: str = "GET", timeout: float = 5.0) -> Result:
    url = base_url.rstrip("/") + path
    req = Request(url, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            try:
                body = json.loads(raw) if raw else None
            except JSONDecodeError:
                body = raw
            return Result(path=path, status=response.status, body=body)
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            body = json.loads(raw) if raw else raw
        except JSONDecodeError:
            body = raw
        return Result(path=path, status=exc.code, body=body)
    except URLError as exc:
        return Result(path=path, status=0, body=str(exc))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-check a running MLX Audio server")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--model-name")
    parser.add_argument("--manage-model", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    results = [_request(args.base_url, "/v1/models", timeout=args.timeout)]

    if args.manage_model and not args.model_name:
        raise SystemExit("--manage-model requires --model-name")

    if args.manage_model and args.model_name:
        encoded = quote(args.model_name, safe="")
        results.append(
            _request(args.base_url, f"/v1/models?model_name={encoded}", method="POST", timeout=args.timeout)
        )
        results.append(
            _request(args.base_url, f"/v1/models?model_name={encoded}", method="DELETE", timeout=args.timeout)
        )

    for result in results:
        print(json.dumps({"path": result.path, "status": result.status, "body": result.body}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
