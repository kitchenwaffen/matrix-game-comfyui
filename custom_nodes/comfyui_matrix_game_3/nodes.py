import os
import re
import subprocess
import time
import uuid
from pathlib import Path

import folder_paths
import numpy as np
from PIL import Image


SAFE_NAME = re.compile(r"[^A-Za-z0-9_-]+")


def _first_frame_to_png(image, destination: Path) -> None:
    frame = image[0].detach().cpu().numpy()
    pixels = np.clip(frame * 255.0, 0, 255).astype(np.uint8)
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(destination, format="PNG")


class MatrixGame3Generate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": (
                            "First-person exploration, stable geometry, "
                            "smooth continuous forward motion."
                        ),
                    },
                ),
                "seed": (
                    "INT",
                    {"default": 42, "min": 0, "max": 0x7FFFFFFF},
                ),
                "num_iterations": (
                    "INT",
                    {"default": 1, "min": 1, "max": 24},
                ),
                "num_inference_steps": (
                    "INT",
                    {"default": 3, "min": 1, "max": 80},
                ),
                "vae_type": (
                    ["mg_lightvae_v2", "mg_lightvae", "wan"],
                    {"default": "mg_lightvae_v2"},
                ),
                "use_int8": ("BOOLEAN", {"default": True}),
                "flash_attention": (
                    ["disabled", "2", "3"],
                    {"default": "disabled"},
                ),
                "filename_prefix": (
                    "STRING",
                    {"default": "matrix-game"},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "generate"
    OUTPUT_NODE = True
    CATEGORY = "Matrix Game 3"

    def generate(
        self,
        image,
        prompt,
        seed,
        num_iterations,
        num_inference_steps,
        vae_type,
        use_int8,
        flash_attention,
        filename_prefix,
    ):
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Matrix-Game prompt is required.")
        if len(prompt) > 4000:
            raise ValueError("Matrix-Game prompt must be at most 4000 characters.")

        repo_dir = Path(
            os.environ.get(
                "MATRIX_GAME_REPO_DIR",
                "/opt/Matrix-Game/Matrix-Game-3",
            )
        )
        model_dir = Path(
            os.environ.get(
                "MATRIX_GAME_MODEL_DIR",
                "/workspace/matrix-game/models/Matrix-Game-3.0",
            )
        )
        python = os.environ.get(
            "MATRIX_GAME_PYTHON",
            "/opt/matrix-game-venv/bin/python",
        )
        required_model = (
            model_dir
            / "base_distilled_model"
            / "diffusion_pytorch_model.safetensors"
        )
        if not required_model.exists():
            log_path = os.environ.get(
                "MATRIX_GAME_HYDRATE_LOG",
                "/workspace/matrix-game/logs/model-hydration.log",
            )
            raise RuntimeError(
                "Matrix-Game 3 model is still hydrating or is missing. "
                f"Check {log_path}."
            )
        if not (repo_dir / "generate.py").exists():
            raise RuntimeError(f"Matrix-Game source is missing at {repo_dir}.")

        safe_prefix = SAFE_NAME.sub("-", filename_prefix).strip("-")[:60]
        safe_prefix = safe_prefix or "matrix-game"
        job_id = f"{safe_prefix}-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        input_dir = Path(folder_paths.get_temp_directory()) / "matrix-game"
        output_dir = Path(folder_paths.get_output_directory()) / "matrix-game"
        image_path = input_dir / f"{job_id}.png"
        output_path = output_dir / f"{job_id}.mp4"
        _first_frame_to_png(image, image_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        command = [
            python,
            str(repo_dir / "generate.py"),
            "--ckpt_dir",
            str(model_dir),
            "--image",
            str(image_path),
            "--prompt",
            prompt,
            "--save_name",
            job_id,
            "--output_dir",
            str(output_dir),
            "--seed",
            str(seed),
            "--num_iterations",
            str(num_iterations),
            "--num_inference_steps",
            str(num_inference_steps),
            "--size",
            "704*1280",
            "--vae_type",
            vae_type,
        ]
        if use_int8:
            command.append("--use_int8")
        if flash_attention != "disabled":
            command.extend(["--fa_version", flash_attention])
        if vae_type == "mg_lightvae":
            command.extend(["--lightvae_pruning_rate", "0.5"])
        elif vae_type == "mg_lightvae_v2":
            command.extend(["--lightvae_pruning_rate", "0.75"])

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        proc = subprocess.run(
            command,
            cwd=repo_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if proc.returncode != 0:
            tail = (proc.stdout or "")[-4000:]
            try:
                listing = "\n".join(
                    sorted(
                        str(p.relative_to(model_dir))
                        + (f" ({p.stat().st_size} bytes)" if p.is_file() else "/")
                        for p in model_dir.rglob("*")
                    )
                )[:4000]
            except Exception as exc:  # noqa: BLE001
                listing = f"<could not list {model_dir}: {exc}>"
            raise RuntimeError(
                f"Matrix-Game generate.py failed (exit {proc.returncode}).\n"
                f"--- generate.py output (tail) ---\n{tail}\n"
                f"--- model dir {model_dir} ---\n{listing}"
            )
        if not output_path.exists() or output_path.stat().st_size == 0:
            tail = (proc.stdout or "")[-2000:]
            raise RuntimeError(
                f"Matrix-Game exited 0 but produced no usable MP4 at "
                f"{output_path}.\n--- output (tail) ---\n{tail}"
            )

        preview = {
            "filename": output_path.name,
            "subfolder": "matrix-game",
            "type": "output",
            "format": "video/mp4",
        }
        return {
            "ui": {"gifs": [preview]},
            "result": (str(output_path),),
        }


NODE_CLASS_MAPPINGS = {"MatrixGame3Generate": MatrixGame3Generate}
NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixGame3Generate": "Matrix Game 3 Generate Video"
}
