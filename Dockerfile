FROM runpod/comfyui@sha256:949b0688db0692b97b9aab9efd1c8f5afe94cfaa32c32008f31bcafcff63baf1

ARG MATRIX_GAME_COMMIT=71c3cd7f741311f8100f6cf9cde942b6c1378d11

RUN git clone https://github.com/SkyworkAI/Matrix-Game.git /opt/Matrix-Game \
    && git -C /opt/Matrix-Game checkout "${MATRIX_GAME_COMMIT}" \
    && test "$(git -C /opt/Matrix-Game rev-parse HEAD)" = "${MATRIX_GAME_COMMIT}"

RUN python3.12 -m venv --system-site-packages /opt/matrix-game-venv \
    && /opt/matrix-game-venv/bin/python -m ensurepip \
    && /opt/matrix-game-venv/bin/python -m pip install --no-cache-dir \
       --constraint /opt/comfyui-runtime-constraints.txt \
       -r /opt/Matrix-Game/Matrix-Game-3/requirements.txt \
    && /opt/matrix-game-venv/bin/python -m pip check

COPY custom_nodes/comfyui_matrix_game_3 \
    /opt/comfyui-baked/custom_nodes/comfyui_matrix_game_3
COPY hydrate_model.py /opt/matrix-game/hydrate_model.py
COPY matrix-start.sh /matrix-start.sh

RUN chmod +x /matrix-start.sh \
    && python3.12 -m py_compile \
       /opt/comfyui-baked/custom_nodes/comfyui_matrix_game_3/nodes.py \
       /opt/matrix-game/hydrate_model.py

ENV MATRIX_GAME_REPO_DIR=/opt/Matrix-Game/Matrix-Game-3 \
    MATRIX_GAME_PYTHON=/opt/matrix-game-venv/bin/python \
    MATRIX_GAME_MODEL_DIR=/workspace/matrix-game/models/Matrix-Game-3.0 \
    MATRIX_GAME_AUTO_DOWNLOAD=1 \
    MATRIX_GAME_HYDRATE_LOG=/workspace/matrix-game/logs/model-hydration.log

LABEL org.opencontainers.image.source="https://github.com/SkyworkAI/Matrix-Game" \
      matrix-game.commit="${MATRIX_GAME_COMMIT}" \
      matrix-game.model="Skywork/Matrix-Game-3.0"

ENTRYPOINT ["/matrix-start.sh"]
