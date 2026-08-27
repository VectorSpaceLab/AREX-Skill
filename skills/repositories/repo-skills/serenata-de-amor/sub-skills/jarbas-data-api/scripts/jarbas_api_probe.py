#!/usr/bin/env python3
"""Safe Jarbas API URL/query helper.

By default this script only builds endpoint paths and explains Jarbas query
normalization. It does not import Django and it does not make network calls.
Pass --request explicitly with an http(s) --base-url if you want a bounded GET.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

REIMBURSEMENT_LIST_PATH = "/api/chamber_of_deputies/reimbursement/"
TRUE_VALUES = {"1", "true"}
TUPLE_FILTER_KEYS = {
    "applicant_id",
    "cnpj_cpf",
    "document_id",
    "issue_date_end",
    "issue_date_start",
    "month",
    "subquota_number",
    "year",
    "state",
}


def clean_cnpj_cpf(value: str) -> str:
    """Replicate Jarbas's query-parameter CNPJ/CPF cleaning behavior."""
    text = str(value)
    for document in re.findall(r"[\d.-]{14}|[\d./-]{18}", text):
        text = text.replace(document, re.sub(r"\D", "", document))
    return text


def format_cnpj(value: str) -> str:
    digits = re.sub(r"\D", "", str(value))
    if len(digits) != 14:
        raise ValueError(f"expected a 14-digit CNPJ, got {len(digits)} digits")
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def parse_bool_like(value: str) -> bool:
    """Jarbas list-view bool parser: only 1/true are true; presence otherwise false."""
    return str(value).lower() in TRUE_VALUES


def split_tuple_filter(value: str) -> Tuple[str, ...]:
    """Replicate the list-view split used for multi-value exact filters."""
    return tuple(part for part in re.split(r"[ ,]+", str(value).strip()) if part)


def encode_query(params: Sequence[Tuple[str, str]]) -> str:
    # Keep commas readable for Jarbas tuple filters; encode slash in formatted CNPJ.
    return urlencode(params, safe=",", quote_via=quote_plus)


def combine_url(base_url: str, path: str, params: Sequence[Tuple[str, str]] = ()) -> str:
    if base_url:
        base = base_url.rstrip("/") + "/"
        url = urljoin(base, path.lstrip("/"))
    else:
        url = path
    if params:
        separator = "&" if "?" in url else "?"
        url = url + separator + encode_query(params)
    return url


def request_get(url: str, timeout: float) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise SystemExit("Refusing --request without an absolute http(s) URL; pass --base-url.")

    req = Request(url, method="GET", headers={"User-Agent": "jarbas-api-probe/1.0"})
    try:
        with urlopen(req, timeout=timeout) as response:  # nosec: explicit --request only
            body = response.read(4096)
            return {
                "status": response.status,
                "content_type": response.headers.get("content-type"),
                "body_prefix": body.decode("utf-8", errors="replace"),
            }
    except HTTPError as exc:
        return {
            "status": exc.code,
            "content_type": exc.headers.get("content-type"),
            "body_prefix": exc.read(4096).decode("utf-8", errors="replace"),
        }
    except URLError as exc:
        return {"error": str(exc)}


def add_common_request_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default="", help="Optional base URL, e.g. http://localhost:8000")
    parser.add_argument("--request", action="store_true", help="Actually perform a bounded GET. Off by default.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout seconds for --request.")
    parser.add_argument("--explain", action="store_true", help="Print normalized query details as JSON after the URL.")


def parse_key_value(items: Iterable[str]) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for item in items:
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        if not key:
            raise argparse.ArgumentTypeError(f"empty key in {item!r}")
        pairs.append((key, value))
    return pairs


def build_reimbursement(args: argparse.Namespace) -> int:
    params: List[Tuple[str, str]] = []
    warnings: List[str] = []

    ordered_values = [
        ("applicant_id", args.applicant_id),
        ("cnpj_cpf", args.cnpj_cpf),
        ("document_id", args.document_id),
        ("issue_date_start", args.issue_date_start),
        ("issue_date_end", args.issue_date_end),
        ("month", args.month),
        ("subquota_number", args.subquota_number),
        ("year", args.year),
        ("state", args.state),
        ("suspicions", args.suspicions),
        ("receipt_url", args.receipt_url),
        ("in_latest_dataset", args.in_latest_dataset),
        ("search", args.search),
        ("order_by", args.order_by),
        ("limit", args.limit),
        ("offset", args.offset),
    ]

    if args.has_receipt is not None and args.receipt_url is None:
        ordered_values[10] = ("receipt_url", args.has_receipt)
        warnings.append("Mapped --has-receipt to receipt_url because the verified view reads receipt_url, not has_receipt.")
    elif args.has_receipt is not None:
        warnings.append("Ignored --has-receipt because --receipt-url was also provided.")

    for key, value in ordered_values:
        if value is None:
            continue
        text = str(value)
        if key == "cnpj_cpf" and not args.preserve_cnpj_format:
            cleaned = clean_cnpj_cpf(text)
            if cleaned != text:
                warnings.append(f"Cleaned cnpj_cpf from {text!r} to {cleaned!r}, matching Jarbas view behavior.")
            text = cleaned
        params.append((key, text))

    params.extend(parse_key_value(args.param or []))

    for key, value in params:
        if key in {"suspicions", "receipt_url", "in_latest_dataset"}:
            parsed = parse_bool_like(value)
            if str(value).lower() not in TRUE_VALUES and str(value).lower() not in {"0", "false"}:
                warnings.append(f"{key}={value!r} is parsed as {parsed}; only '1' and 'true' are true.")
        if key == "in_latest_dataset":
            warnings.append("in_latest_dataset is listed in public prose but is not backed by the verified queryset/model surface.")
        if key == "has_receipt":
            warnings.append("has_receipt is a documentation-era name; the verified view reads receipt_url.")
        if key == "search":
            warnings.append("search requires PostgreSQL search vectors populated from loaded data; SQLite is not equivalent.")
        if key == "order_by" and value != "probability":
            warnings.append("Only order_by=probability changes ordering in the verified view.")

    url = combine_url(args.base_url, REIMBURSEMENT_LIST_PATH, params)
    print(url)

    if args.explain:
        tuple_filters = {key: split_tuple_filter(value) for key, value in params if key in TUPLE_FILTER_KEYS}
        bool_params = {key: parse_bool_like(value) for key, value in params if key in {"suspicions", "receipt_url", "in_latest_dataset"}}
        print(json.dumps({
            "path": REIMBURSEMENT_LIST_PATH,
            "query_params": params,
            "tuple_filter_values": tuple_filters,
            "boolean_params": bool_params,
            "warnings": warnings,
        }, indent=2, sort_keys=True))

    if args.request:
        print(json.dumps({"request": request_get(url, args.timeout)}, indent=2, sort_keys=True))
    return 0


def build_endpoint(args: argparse.Namespace) -> int:
    params: List[Tuple[str, str]] = []
    warnings: List[str] = []

    if args.endpoint == "reimbursement-detail":
        require(args.document_id, "--document-id is required")
        path = f"/api/chamber_of_deputies/reimbursement/{args.document_id}/"
    elif args.endpoint == "receipt":
        require(args.document_id, "--document-id is required")
        path = f"/api/chamber_of_deputies/reimbursement/{args.document_id}/receipt/"
        if args.force:
            params.append(("force", "1"))
            warnings.append("Any present force parameter triggers a receipt refetch.")
    elif args.endpoint == "same-day":
        require(args.document_id, "--document-id is required")
        path = f"/api/chamber_of_deputies/reimbursement/{args.document_id}/same_day/"
    elif args.endpoint == "applicant":
        path = "/api/chamber_of_deputies/applicant/"
        if args.q is not None:
            params.append(("q", args.q))
    elif args.endpoint == "subquota":
        path = "/api/chamber_of_deputies/subquota/"
        if args.q is not None:
            params.append(("q", args.q))
    elif args.endpoint == "company":
        require(args.cnpj, "--cnpj is required")
        digits = re.sub(r"\D", "", args.cnpj)
        formatted = format_cnpj(digits)
        path = f"/api/company/{digits}/"
        warnings.append(f"Company path uses digits; Jarbas looks up stored formatted CNPJ {formatted!r}.")
    elif args.endpoint == "healthcheck":
        path = "/healthcheck/"
    else:  # pragma: no cover - argparse choices prevent this
        raise SystemExit(f"unknown endpoint {args.endpoint}")

    if args.limit is not None:
        params.append(("limit", str(args.limit)))
    if args.offset is not None:
        params.append(("offset", str(args.offset)))

    url = combine_url(args.base_url, path, params)
    print(url)
    if args.explain:
        print(json.dumps({"path": path, "query_params": params, "warnings": warnings}, indent=2, sort_keys=True))
    if args.request:
        print(json.dumps({"request": request_get(url, args.timeout)}, indent=2, sort_keys=True))
    return 0


def require(value: object, message: str) -> None:
    if value in (None, ""):
        raise SystemExit(message)


def clean_document(args: argparse.Namespace) -> int:
    cleaned = clean_cnpj_cpf(args.value)
    data = {"input": args.value, "cleaned": cleaned}
    digits = re.sub(r"\D", "", cleaned)
    if len(digits) == 14:
        data["formatted_cnpj"] = format_cnpj(digits)
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


def smoke(_: argparse.Namespace) -> int:
    assert clean_cnpj_cpf("12.345.678/9012-34") == "12345678901234"
    assert clean_cnpj_cpf("020.020.020-02") == "02002002002"
    assert format_cnpj("07575651000159") == "07.575.651/0001-59"
    assert split_tuple_filter("42,84 126, 168") == ("42", "84", "126", "168")
    assert parse_bool_like("true") is True
    assert parse_bool_like("1") is True
    assert parse_bool_like("false") is False
    assert parse_bool_like("0") is False
    demo = combine_url(
        "",
        REIMBURSEMENT_LIST_PATH,
        [
            ("document_id", "111111,222222"),
            ("cnpj_cpf", clean_cnpj_cpf("07.575.651/0001-59")),
            ("suspicions", "true"),
            ("order_by", "probability"),
        ],
    )
    assert "document_id=111111,222222" in demo
    assert "cnpj_cpf=07575651000159" in demo
    print("smoke ok")
    print(demo)
    return 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and explain Jarbas API URLs without network access by default.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    clean = subparsers.add_parser("clean-document", help="Clean a CNPJ/CPF the way the reimbursement filter does.")
    clean.add_argument("value", help="Formatted or unformatted CNPJ/CPF value")
    clean.set_defaults(func=clean_document)

    build = subparsers.add_parser("build-reimbursement", help="Build a reimbursement-list URL and explain query behavior.")
    add_common_request_args(build)
    build.add_argument("--applicant-id")
    build.add_argument("--cnpj-cpf")
    build.add_argument("--preserve-cnpj-format", action="store_true", help="Keep formatted cnpj_cpf in the URL instead of normalizing to digits.")
    build.add_argument("--document-id", help="One value or comma/space-separated values, e.g. 42,84")
    build.add_argument("--issue-date-start")
    build.add_argument("--issue-date-end")
    build.add_argument("--month")
    build.add_argument("--subquota-number")
    build.add_argument("--year")
    build.add_argument("--state")
    build.add_argument("--suspicions", help="Jarbas true values: 1 or true; any other present value is false.")
    build.add_argument("--receipt-url", help="Filter rows with/without stored receipt_url.")
    build.add_argument("--has-receipt", help="Documentation-era alias; mapped to receipt_url if receipt-url is absent.")
    build.add_argument("--in-latest-dataset")
    build.add_argument("--search")
    build.add_argument("--order-by")
    build.add_argument("--limit")
    build.add_argument("--offset")
    build.add_argument("--param", action="append", help="Extra raw KEY=VALUE query parameter. May be repeated.")
    build.set_defaults(func=build_reimbursement)

    endpoint = subparsers.add_parser("build-endpoint", help="Build non-list endpoint URLs.")
    add_common_request_args(endpoint)
    endpoint.add_argument("endpoint", choices=["reimbursement-detail", "receipt", "same-day", "applicant", "subquota", "company", "healthcheck"])
    endpoint.add_argument("--document-id")
    endpoint.add_argument("--cnpj", help="Company CNPJ, formatted or digits; endpoint path will use 14 digits.")
    endpoint.add_argument("--q", help="q filter for applicant or subquota lists")
    endpoint.add_argument("--force", action="store_true", help="Add force=1 for receipt endpoint")
    endpoint.add_argument("--limit")
    endpoint.add_argument("--offset")
    endpoint.set_defaults(func=build_endpoint)

    smoke_parser = subparsers.add_parser("smoke", help="Run deterministic self-tests and print a demo URL.")
    smoke_parser.set_defaults(func=smoke)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
