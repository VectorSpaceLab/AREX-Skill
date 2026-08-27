#!/usr/bin/env python3
"""Skill-owned HTTP Bot HMAC helper.

Safe offline subcommands: sign, verify, payload. Network subcommands post/reset
only run when explicitly invoked.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
import time
import uuid
import urllib.request

HEADER_TIMESTAMP = 'X-LB-Timestamp'
HEADER_SIGNATURE = 'X-LB-Signature'
HEADER_IDEMPOTENCY = 'X-LB-Idempotency-Key'


def sign(secret: str, body: bytes, timestamp: int | None = None) -> tuple[str, str]:
    ts = str(timestamp if timestamp is not None else int(time.time()))
    mac = hmac.new(secret.encode(), f'{ts}.'.encode() + body, hashlib.sha256)
    return ts, 'sha256=' + mac.hexdigest()


def verify(secret: str, body: bytes, timestamp: str, signature: str, replay_window: int = 300) -> bool:
    try:
        ts_int = int(float(timestamp))
    except ValueError:
        return False
    if abs(int(time.time()) - ts_int) > replay_window:
        return False
    _, expected = sign(secret, body, ts_int)
    return hmac.compare_digest(expected, signature)


def payload(session: str, text: str | None, session_type: str = 'person') -> dict:
    data = {'session_id': session, 'session_type': session_type}
    if text is not None:
        data['message'] = [{'type': 'Plain', 'text': text}]
    return data


def post(url: str, secret: str, data: dict, idempotency: bool = True, timeout: float = 30.0) -> None:
    body = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
    ts, sig = sign(secret, body)
    headers = {'Content-Type': 'application/json', HEADER_TIMESTAMP: ts, HEADER_SIGNATURE: sig}
    if idempotency:
        headers[HEADER_IDEMPOTENCY] = uuid.uuid4().hex
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - explicit user URL helper
        print(resp.status, resp.read().decode(errors='replace'))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='LangBot HTTP Bot HMAC helper')
    sub = parser.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('sign')
    s.add_argument('--secret', required=True)
    s.add_argument('--body', required=True, help='Raw JSON/text body to sign')
    s.add_argument('--timestamp', type=int)

    v = sub.add_parser('verify')
    v.add_argument('--secret', required=True)
    v.add_argument('--body', required=True)
    v.add_argument('--timestamp', required=True)
    v.add_argument('--signature', required=True)

    p = sub.add_parser('payload')
    p.add_argument('--session', required=True)
    p.add_argument('--session-type', default='person', choices=['person', 'group'])
    p.add_argument('--text', required=True)

    for name in ('post', 'sync', 'reset'):
        c = sub.add_parser(name)
        c.add_argument('--url', required=True, help='Base bot URL, e.g. https://host/bots/<BOT_UUID>')
        c.add_argument('--secret', required=True)
        c.add_argument('--session', required=True)
        c.add_argument('--session-type', default='person', choices=['person', 'group'])
        c.add_argument('--timeout', type=float, default=30.0)
        if name != 'reset':
            c.add_argument('--text', required=True)

    args = parser.parse_args(argv)
    if args.cmd == 'sign':
        ts, sig = sign(args.secret, args.body.encode(), args.timestamp)
        print(json.dumps({'timestamp': ts, 'signature': sig}, indent=2))
    elif args.cmd == 'verify':
        ok = verify(args.secret, args.body.encode(), args.timestamp, args.signature)
        print('OK' if ok else 'FAIL')
        return 0 if ok else 1
    elif args.cmd == 'payload':
        print(json.dumps(payload(args.session, args.text, args.session_type), ensure_ascii=False, indent=2))
    elif args.cmd == 'post':
        post(args.url.rstrip('/'), args.secret, payload(args.session, args.text, args.session_type), True, args.timeout)
    elif args.cmd == 'sync':
        post(args.url.rstrip('/') + '/sync', args.secret, payload(args.session, args.text, args.session_type), False, args.timeout)
    elif args.cmd == 'reset':
        post(args.url.rstrip('/') + '/reset', args.secret, payload(args.session, None, args.session_type), False, args.timeout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
