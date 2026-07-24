# Experimental Matrix-Game 3 ComfyUI image

This build extends the exact surviving RunPod ComfyUI image and adds a pinned
Matrix-Game 3 subprocess node. It is experimental until an MP4 is generated
through ComfyUI on a supported GPU.

Build:

```powershell
agent_system\tools\build_matrix_comfyui_image.cmd
```

Runtime expectations:

- Mount persistent storage at `/workspace`.
- Expose `8188/http`, `8080/http`, `8888/http`, and `22/tcp`.
- Model hydration begins in the background on first boot and writes
  `/workspace/matrix-game/logs/model-hydration.log`.
- The node refuses to start generation until the distilled checkpoint exists.
- The first validation workflow is `workflow_api.json`.
- Use an A/H-series GPU for the first official-support test.

The public Cloudflare Worker must not be switched to this contract until the
workflow has completed successfully and produced a valid MP4.
