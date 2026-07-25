#!/usr/bin/env bash
set -euo pipefail

# The runpod/comfyui base copies /opt/comfyui-baked to
# /workspace/runpod-slim/ComfyUI on FIRST boot only. Since /workspace is a
# persistent network volume, an image update to our custom node would otherwise
# never reach an existing volume. Refresh it from the image on every boot.
COMFY_VOL=/workspace/runpod-slim/ComfyUI
if [[ -d "${COMFY_VOL}/custom_nodes" ]]; then
  echo "Refreshing comfyui_matrix_game_3 on the persistent volume from the image."
  rm -rf "${COMFY_VOL}/custom_nodes/comfyui_matrix_game_3"
  cp -r /opt/comfyui-baked/custom_nodes/comfyui_matrix_game_3 \
        "${COMFY_VOL}/custom_nodes/"
fi

if [[ "${MATRIX_GAME_AUTO_DOWNLOAD:-1}" == "1" ]]; then
  mkdir -p "$(dirname "${MATRIX_GAME_HYDRATE_LOG}")"
  if [[ ! -f "${MATRIX_GAME_MODEL_DIR}/base_distilled_model/diffusion_pytorch_model.safetensors" ]]; then
    echo "Starting Matrix-Game 3 model hydration in the background."
    nohup /opt/matrix-game-venv/bin/python /opt/matrix-game/hydrate_model.py \
      >> "${MATRIX_GAME_HYDRATE_LOG}" 2>&1 &
  fi
fi

exec /start.sh "$@"
