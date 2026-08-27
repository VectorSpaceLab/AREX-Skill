#!/usr/bin/env python3
"""Self-contained interactive WorldGen demo built on the public Python API.

The helper mirrors the repository demo without depending on the original
checkout. It generates a scene, starts a local Viser viewer, and provides
camera-path and novel-view export controls.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Tuple

import imageio
import numpy as np
import open3d as o3d
import torch
import trimesh
import viser
from PIL import Image
from scipy.spatial.transform import Rotation as R
from tqdm import tqdm

from worldgen import WorldGen
from worldgen.utils.splat_utils import SplatFile


def quaternion_slerp(q1, q2, t):
    """Spherical linear interpolation between wxyz quaternions."""
    q1 = np.asarray(q1, dtype=float)
    q2 = np.asarray(q2, dtype=float)
    q1 = q1 / np.linalg.norm(q1)
    q2 = q2 / np.linalg.norm(q2)
    dot = float(np.sum(q1 * q2))
    if dot < 0.0:
        q2 = -q2
        dot = -dot
    dot = min(1.0, max(-1.0, dot))
    theta = np.arccos(dot)
    sin_theta = np.sin(theta)
    if sin_theta < 1e-6:
        return q1 * (1 - t) + q2 * t
    s1 = np.sin((1 - t) * theta) / sin_theta
    s2 = np.sin(t * theta) / sin_theta
    return q1 * s1 + q2 * s2


class WorldGenDemo:
    def __init__(self, args: argparse.Namespace):
        if not torch.cuda.is_available():
            raise RuntimeError(
                "The WorldGen demo requires a CUDA-capable PyTorch install; "
                "use scripts/check_worldgen_env.py to diagnose the environment."
            )

        self.server = viser.ViserServer()
        self.server.scene.set_up_direction("-y")
        self.server.scene.enable_default_lights(False)
        self.device = torch.device("cuda")
        self.args = args
        self.frames = []
        self.start_camera = None
        self.return_mesh = bool(args.return_mesh)

        if args.return_mesh and args.inpaint_bg:
            raise ValueError("--inpaint_bg is not supported with --return_mesh")

        if args.use_sharp:
            print("INFO: using the experimental ml-sharp Gaussian path")
        if args.inpaint_bg:
            print("WARNING: background inpainting is experimental")

        mode = "i2s" if args.image else "t2s"
        self.worldgen = WorldGen(
            mode=mode,
            use_sharp=args.use_sharp,
            inpaint_bg=args.inpaint_bg,
            resolution=args.resolution,
            device=self.device,
            low_vram=args.low_vram,
        )

    def add_camera_frustum(
        self,
        name: str,
        fov: float,
        aspect: float,
        scale: float = 0.2,
        position: Tuple[float, float, float] = (0, 0, 0),
        wxyz: Tuple[float, float, float, float] = (1, 0, 0, 0),
        color: Tuple[int, int, int] = (0, 255, 0),
        visible: bool = True,
    ):
        return self.server.scene.add_camera_frustum(
            name,
            fov=fov,
            aspect=aspect,
            scale=scale,
            position=position,
            wxyz=wxyz,
            color=color,
            visible=visible,
        )

    def add_gaussian_splats(self, splat: SplatFile):
        if self.args.save_scene:
            output = Path(self.args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            splat.save(str(output / "splat.ply"))
        self.scene_gs_handle = self.server.scene.add_gaussian_splats(
            "/scene_gs",
            centers=splat.centers,
            rgbs=splat.rgbs,
            opacities=splat.opacities,
            covariances=splat.covariances,
        )

    def add_mesh(self, mesh: o3d.geometry.TriangleMesh):
        if self.args.save_scene:
            output = Path(self.args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            o3d.io.write_triangle_mesh(str(output / "mesh.glb"), mesh)
        vertices = np.asarray(mesh.vertices)
        faces = np.asarray(mesh.triangles)
        colors = np.asarray(mesh.vertex_colors)
        trimesh_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        if colors.size:
            trimesh_mesh.visual.vertex_colors = colors
        self.scene_mesh_handle = self.server.scene.add_mesh_trimesh(
            name="/scene_mesh", mesh=trimesh_mesh
        )

    def add_original_camera(self):
        height, width = 1080, 1920
        fov = np.deg2rad(90)
        self.original_camera = self.server.scene.add_camera_frustum(
            "original_camera", fov, width / height
        )
        self.init_h, self.init_w = height, width
        self.original_camera.visible = False

    def prepare_render_visibility(self):
        self.original_camera.visible = False
        for frame in self.frames:
            frame.visible = False
        if hasattr(self, "gs_transform_controls"):
            self.gs_transform_controls.scale = 0.0

    def restore_render_visibility(self):
        self.original_camera.visible = True
        for frame in self.frames:
            frame.visible = True
        if hasattr(self, "gs_transform_controls"):
            self.gs_transform_controls.scale = 2.0

    def save_novel_views(self, client):
        render_h = self.render_height_input.value
        render_w = self.render_width_input.value
        render_fov_deg = self.render_fov_input.value
        render_fov_rad = np.deg2rad(render_fov_deg)
        output = Path(self.args.output_dir)
        image_dir = output / "images"
        image_dir.mkdir(parents=True, exist_ok=True)

        print(f"Saving novel views ({render_h}x{render_w}, FoV {render_fov_deg}°)")
        self.prepare_render_visibility()
        writer = imageio.get_writer(str(output / "rgb.mp4"), fps=30)
        try:
            for index, frame in tqdm(enumerate(self.frames), total=len(self.frames)):
                image = client.get_render(
                    height=render_h,
                    width=render_w,
                    wxyz=frame.wxyz,
                    position=frame.position,
                    fov=render_fov_rad,
                )
                imageio.imwrite(str(image_dir / f"{index:04d}.png"), image)
                writer.append_data(image)
        finally:
            writer.close()
            self.restore_render_visibility()

    def add_interpolated_cameras(self, client):
        current_wxyz = client.camera.wxyz
        current_position = client.camera.position
        steps = self.interpolation_steps.value
        current_fov = self.original_camera.fov
        current_aspect = self.original_camera.aspect

        def click_handler_for(frame):
            def click_handler(_):
                with client.atomic():
                    client.camera.wxyz = frame.wxyz
                    client.camera.position = frame.position
                    client.camera.fov = frame.fov
            return click_handler

        if self.start_camera is None:
            self.start_camera = self.add_camera_frustum(
                "/start_camera",
                fov=current_fov,
                aspect=current_aspect,
                position=current_position,
                wxyz=current_wxyz,
                color=(0, 0, 0),
            )
            self.start_camera.on_click(click_handler_for(self.start_camera))
            self.frames.append(self.start_camera)
            return

        start_wxyz = self.start_camera.wxyz
        start_position = self.start_camera.position
        for index in range(1, steps + 1):
            t = index / steps
            eased = t * t * (3 - 2 * t)
            position = eased * current_position + (1 - eased) * start_position
            wxyz = quaternion_slerp(start_wxyz, current_wxyz, eased)
            color = (0, int(150 * (1 - t) + 255 * t), int(255 * (1 - t)))
            frame = self.server.scene.add_camera_frustum(
                f"/camera_{index}",
                fov=current_fov,
                aspect=current_aspect,
                scale=0.2,
                wxyz=wxyz,
                position=position,
                color=color,
            )
            frame.on_click(click_handler_for(frame))
            self.frames.append(frame)
        print(f"Added camera path with {steps + 1} cameras")

    def create_ui(self, client):
        initial_fov = self.original_camera.fov
        client.camera.position = (0, 0, 0)
        client.camera.wxyz = (1, 0, 0, 0)
        client.camera.fov = initial_fov
        client.camera.far = 10000
        client.camera.near = 0.01
        client.camera.look_at = (0, 0, 0.01)

        with client.gui.add_folder("Camera Path"):
            self.interpolation_steps = client.gui.add_slider(
                "Interpolation Steps", min=1, max=1000, step=1, initial_value=120
            )
            self.add_camera_path_button = client.gui.add_button("Generate Camera Path")

        with client.gui.add_folder("Render Settings"):
            self.render_fov_input = client.gui.add_number(
                "Render FoV (deg)", initial_value=np.rad2deg(initial_fov), min=1.0, max=179.0, step=5
            )
            self.render_height_input = client.gui.add_number(
                "Render Height", initial_value=self.init_h, min=64, max=4096, step=1
            )
            self.render_width_input = client.gui.add_number(
                "Render Width", initial_value=self.init_w, min=64, max=4096, step=1
            )
            self.save_button = client.gui.add_button("Save Novel Views")

            @self.render_fov_input.on_update
            def _(_value):
                client.camera.fov = np.deg2rad(self.render_fov_input.value)

    def generate_scene(self):
        if self.args.pano_image:
            pano = Image.open(self.args.pano_image).convert("RGB")
            pano = pano.resize((2048, 1024))
            return self.worldgen._generate_world(pano, return_mesh=self.return_mesh)
        if self.args.image:
            image = Image.open(self.args.image).convert("RGB")
            return self.worldgen.generate_world(
                self.args.prompt or "", image, return_mesh=self.return_mesh
            )
        return self.worldgen.generate_world(
            self.args.prompt or "", return_mesh=self.return_mesh
        )

    def run(self):
        print("Generating the world; model downloads may take time on first use")
        scene = self.generate_scene()
        if self.return_mesh:
            self.add_mesh(scene)
        else:
            self.add_gaussian_splats(scene)
            self.server.scene.set_background_image(np.zeros((1, 1, 3)))
        self.add_original_camera()
        print("World generated. Open http://localhost:8080 in a browser.")

        @self.server.on_client_connect
        def connect(client: viser.ClientHandle) -> None:
            self.create_ui(client)

            @self.original_camera.on_click
            def _(_event):
                with client.atomic():
                    client.camera.wxyz = self.original_camera.wxyz
                    client.camera.position = self.original_camera.position
                    client.camera.fov = self.original_camera.fov

            @self.save_button.on_click
            def _(_event):
                self.save_novel_views(client)

            @self.add_camera_path_button.on_click
            def _(_event):
                self.add_interpolated_cameras(client)

        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("Exiting...")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WorldGen interactive 3D scene demo")
    parser.add_argument("--prompt", "-p", type=str, help="Text prompt for world generation")
    parser.add_argument("--image", "-i", type=str, help="Input image for image-to-scene generation")
    parser.add_argument("--output_dir", "-o", default="output", help="Output directory")
    parser.add_argument("--resolution", "-r", type=int, default=1600, help="Generated panorama width")
    parser.add_argument("--pano_image", type=str, help="Input equirectangular panorama image")
    parser.add_argument("--use_sharp", action="store_true", help="Use experimental ml-sharp")
    parser.add_argument("--inpaint_bg", action="store_true", help="Use experimental background inpainting")
    parser.add_argument("--return_mesh", action="store_true", help="Return and display an Open3D mesh")
    parser.add_argument("--save_scene", action="store_true", help="Save splat.ply or mesh.glb")
    parser.add_argument("--low_vram", action="store_true", help="Enable low-VRAM model loading")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("WorldGen requires CUDA; run check_worldgen_env.py first.")
    if not args.low_vram:
        memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if memory_gb < 24:
            print(f"Detected {memory_gb:.1f}GB VRAM; enabling low-VRAM mode")
            args.low_vram = True
    WorldGenDemo(args).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
