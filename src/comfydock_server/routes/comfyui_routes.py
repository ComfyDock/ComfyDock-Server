from fastapi import APIRouter, HTTPException
from comfydock_core.comfyui_integration import check_comfyui_path, try_install_comfyui

router = APIRouter(prefix="/comfyui", tags=["comfyui"])


@router.post("/validate-path")
def validate_path_endpoint(obj: dict):
    """
    Check if the provided path contains a valid ComfyUI installation.
    """
    try:
        valid_path = check_comfyui_path(obj["path"])
        return {"valid_comfyui_path": str(valid_path)}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Path validation failed",
                "error": str(e),
                "path": obj.get("path", "")
            }
        )


@router.post("/install")
def install_comfyui_endpoint(obj: dict):
    """
    Attempt to install (clone) ComfyUI into the given path if no valid installation exists.
    """
    try:
        path = try_install_comfyui(obj["path"])
        return {"status": "success", "path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))