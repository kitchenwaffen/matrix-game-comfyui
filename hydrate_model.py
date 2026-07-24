import os
from pathlib import Path

from huggingface_hub import snapshot_download


MODEL_REPO = "Skywork/Matrix-Game-3.0"
MODEL_DIR = Path(
    os.environ.get(
        "MATRIX_GAME_MODEL_DIR",
        "/workspace/matrix-game/models/Matrix-Game-3.0",
    )
)
MARKER = MODEL_DIR / ".matrix-game-3.complete"


def main() -> None:
    if MARKER.exists():
        print(f"MODEL READY {MODEL_DIR}", flush=True)
        return

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"HYDRATING {MODEL_REPO} -> {MODEL_DIR}", flush=True)
    snapshot_download(
        repo_id=MODEL_REPO,
        local_dir=str(MODEL_DIR),
        resume_download=True,
    )
    required = (
        MODEL_DIR
        / "base_distilled_model"
        / "diffusion_pytorch_model.safetensors"
    )
    if not required.exists():
        raise RuntimeError(f"Model hydration finished without {required}")
    MARKER.write_text("Skywork/Matrix-Game-3.0\n", encoding="utf-8")
    print(f"ALL DONE MODEL READY {MODEL_DIR}", flush=True)


if __name__ == "__main__":
    main()
