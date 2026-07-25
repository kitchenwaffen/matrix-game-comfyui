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

# Optional Wan 2.2 TI2V-5B image-to-video hydration (native ComfyUI, no custom
# node). Gated on HYDRATE_WAN so only Wan pods pull it. Runs in the BACKGROUND
# so ComfyUI (started by exec /start.sh below) comes up immediately.
if [[ "${HYDRATE_WAN:-0}" == "1" ]]; then
  WM="${COMFY_VOL}/models"
  mkdir -p "${WM}/diffusion_models" "${WM}/text_encoders" "${WM}/vae"
  WB=https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files
  WL=/workspace/wan-download.log
  (
    for P in diffusion_models/wan2.2_ti2v_5B_fp16.safetensors text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors vae/wan2.2_vae.safetensors; do
      D="${WM}/${P}"
      if [[ ! -s "$D" ]]; then
        echo "$(date -u) downloading ${P}" >> "$WL"
        wget -q -c -O "${D}.part" "${WB}/${P}" && mv -f "${D}.part" "$D" && echo "$(date -u) done ${P}" >> "$WL"
      fi
    done
    echo "$(date -u) ALL WAN MODELS READY" >> "$WL"
  ) &
fi

exec /start.sh "$@"
