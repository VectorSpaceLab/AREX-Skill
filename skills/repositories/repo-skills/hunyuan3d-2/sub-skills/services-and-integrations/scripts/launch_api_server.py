#!/usr/bin/env python3
"""Self-contained FastAPI launcher for Hunyuan3D-2 generation.

This is an adapted, compact server based on the repository's api_server.py
semantics. It uses only installed Python packages and model weights; it does
not require the original checkout once this skill is copied.
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch a Hunyuan3D-2 FastAPI generation server.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Use 0.0.0.0 only when exposing intentionally.")
    parser.add_argument("--port", type=int, default=8080, help="Bind port.")
    parser.add_argument("--model-path", default="tencent/Hunyuan3D-2mini", help="Shape model repo id or local path.")
    parser.add_argument("--subfolder", default="hunyuan3d-dit-v2-mini-turbo", help="Shape model subfolder.")
    parser.add_argument("--tex-model-path", default="tencent/Hunyuan3D-2", help="Texture model repo id or local path.")
    parser.add_argument("--tex-subfolder", default="hunyuan3d-paint-v2-0-turbo", help="Texture model subfolder.")
    parser.add_argument("--device", default="cuda", help="Torch device for generation.")
    parser.add_argument("--enable-tex", action="store_true", help="Load paint pipeline and honor texture=true requests.")
    parser.add_argument("--enable-flashvdm", action="store_true", help="Enable FlashVDM decoder for the shape pipeline.")
    parser.add_argument("--mc-algo", default="mc", help="Marching-cubes backend passed to FlashVDM/generation.")
    parser.add_argument("--cache-dir", default="hunyuan3d_api_cache", help="Directory for generated outputs.")
    parser.add_argument("--log-level", default="info", help="uvicorn log level.")
    parser.add_argument("--dry-run", action="store_true", help="Print launch plan without importing models or starting the server.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    plan = vars(args).copy()
    if args.dry_run:
        print(json.dumps({"status": "dry-run", "plan": plan}, indent=2, sort_keys=True))
        return
    if args.device == "cpu":
        raise SystemExit("Real Hunyuan3D generation is CUDA-scoped in this skill; use --device cuda.")

    import tempfile
    import threading
    import traceback
    import uuid
    from io import BytesIO

    import torch
    import trimesh
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse
    from PIL import Image

    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import DegenerateFaceRemover, FaceReducer, FloaterRemover, Hunyuan3DDiTFlowMatchingPipeline
    from hy3dgen.texgen import Hunyuan3DPaintPipeline

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    def image_from_b64(value: str) -> Image.Image:
        return Image.open(BytesIO(base64.b64decode(value)))

    class Worker:
        def __init__(self) -> None:
            self.rembg = BackgroundRemover()
            self.shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
                args.model_path,
                subfolder=args.subfolder,
                use_safetensors=True,
                device=args.device,
            )
            if args.enable_flashvdm:
                self.shape.enable_flashvdm(mc_algo=args.mc_algo)
            self.paint = None
            if args.enable_tex:
                self.paint = Hunyuan3DPaintPipeline.from_pretrained(args.tex_model_path, subfolder=args.tex_subfolder)

        @torch.inference_mode()
        def generate(self, uid: str, params: dict) -> Path:
            if "image" not in params:
                if "text" in params:
                    raise ValueError("Text-to-3D is not enabled in this compact server; provide image or customize a t2i pipeline.")
                raise ValueError("No input image provided")
            raw_image = image_from_b64(params["image"])
            if raw_image.mode == "RGB":
                image = self.rembg(raw_image)
            else:
                image = raw_image.convert("RGBA")

            if "mesh" in params:
                mesh = trimesh.load(BytesIO(base64.b64decode(params["mesh"])), file_type="glb")
            else:
                generator = torch.Generator(args.device).manual_seed(int(params.get("seed", 1234)))
                mesh = self.shape(
                    image=image,
                    generator=generator,
                    octree_resolution=int(params.get("octree_resolution", 128)),
                    num_inference_steps=int(params.get("num_inference_steps", 5)),
                    guidance_scale=float(params.get("guidance_scale", 5.0)),
                    mc_algo=params.get("mc_algo", args.mc_algo),
                    output_type="trimesh",
                )[0]

            if params.get("texture", False):
                if self.paint is None:
                    raise ValueError("texture=true requires launching with --enable-tex")
                mesh = FloaterRemover()(mesh)
                mesh = DegenerateFaceRemover()(mesh)
                mesh = FaceReducer()(mesh, max_facenum=int(params.get("face_count", 40000)))
                mesh = self.paint(mesh, image)

            suffix = str(params.get("type", "glb")).lstrip(".") or "glb"
            with tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=False) as tmp:
                mesh.export(tmp.name)
                normalized = trimesh.load(tmp.name)
            output = cache_dir / f"{uid}.{suffix}"
            normalized.export(output)
            torch.cuda.empty_cache()
            return output

    worker = Worker()
    app = FastAPI(title="Hunyuan3D-2 compact API")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    @app.post("/generate")
    async def generate(request: Request):
        params = await request.json()
        uid = str(uuid.uuid4())
        try:
            path = worker.generate(uid, params)
            return FileResponse(str(path))
        except Exception as exc:  # noqa: BLE001 - service boundary
            traceback.print_exc()
            return JSONResponse({"text": str(exc), "error_code": 1}, status_code=404)

    @app.post("/send")
    async def send(request: Request):
        params = await request.json()
        uid = str(uuid.uuid4())
        threading.Thread(target=lambda: worker.generate(uid, params), daemon=True).start()
        return JSONResponse({"uid": uid}, status_code=200)

    @app.get("/status/{uid}")
    async def status(uid: str):
        path = cache_dir / f"{uid}.glb"
        if not path.exists():
            return JSONResponse({"status": "processing"}, status_code=200)
        return JSONResponse({"status": "completed", "model_base64": base64.b64encode(path.read_bytes()).decode("utf-8")})

    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
