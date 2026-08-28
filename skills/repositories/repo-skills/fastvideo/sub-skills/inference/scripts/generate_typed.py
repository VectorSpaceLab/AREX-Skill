#!/usr/bin/env python3
"""Small typed-API generation wrapper; downloads model weights and writes requested output."""
import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument("--num-frames", type=int, default=81)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--num-gpus", type=int, default=1)
    parser.add_argument("--return-frames", action="store_true")
    args = parser.parse_args()
    if min(args.num_frames, args.height, args.width, args.steps, args.num_gpus) <= 0:
        parser.error("frame, dimension, step, and GPU counts must be positive")
    from fastvideo import VideoGenerator
    generator = VideoGenerator.from_pretrained(args.model, num_gpus=args.num_gpus)
    result = generator.generate({
        "prompt": args.prompt,
        "sampling": {
            "seed": args.seed,
            "num_frames": args.num_frames,
            "height": args.height,
            "width": args.width,
            "num_inference_steps": args.steps,
        },
        "output": {
            "output_path": args.output_dir,
            "save_video": True,
            "return_frames": args.return_frames,
        },
    })
    print(json.dumps({"video_path": getattr(result, "video_path", None), "size": getattr(result, "size", None)}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
