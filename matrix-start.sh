#!/usr/bin/env bash
set -euo pipefail

if [[ "${MATRIX_GAME_AUTO_DOWNLOAD:-1}" == "1" ]]; then
  mkdir -p "$(dirname "${MATRIX_GAME_HYDRATE_LOG}")"
  if [[ ! -f "${MATRIX_GAME_MODEL_DIR}/base_distilled_model/diffusion_pytorch_model.safetensors" ]]; then
    echo "Starting Matrix-Game 3 model hydration in the background."
    nohup /opt/matrix-game-venv/bin/python /opt/matrix-game/hydrate_model.py \
      >> "${MATRIX_GAME_HYDRATE_LOG}" 2>&1 &
  fi
fi

exec /start.sh "$@"
