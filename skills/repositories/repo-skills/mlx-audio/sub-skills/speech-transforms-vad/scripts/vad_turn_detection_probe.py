from __future__ import annotations

import argparse
import json

from mlx_audio.realtime_vad import ServerVadConfig, TurnDetector


def _parse_probabilities(value: str) -> list[float]:
    return [float(item) for item in value.split(",") if item.strip()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe synthetic VAD turn detection")
    parser.add_argument("--probabilities", required=True, help="Comma-separated frame probabilities")
    parser.add_argument("--frame-ms", type=float, default=20.0)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--prefix-padding-ms", type=int, default=300)
    parser.add_argument("--silence-duration-ms", type=int, default=500)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    detector = TurnDetector(
        ServerVadConfig(
            threshold=args.threshold,
            prefix_padding_ms=args.prefix_padding_ms,
            silence_duration_ms=args.silence_duration_ms,
        )
    )
    events = []
    for probability in _parse_probabilities(args.probabilities):
        for event in detector.push(probability, args.frame_ms):
            events.append({"kind": event.kind.value, "audio_ms": event.audio_ms})
    print(json.dumps(events, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
