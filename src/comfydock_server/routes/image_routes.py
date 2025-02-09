import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from .dependencies import get_env_manager, get_config
from ..config import ServerConfig
from comfydock_core.docker_interface import (
    DockerInterfaceImageNotFoundError,
    DockerInterfaceError,
)
import requests

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/tags")
def get_image_tags(config: ServerConfig = Depends(get_config)):
    try:
        response = requests.get(config.dockerhub_images_url)
        return {"tags": [tag["name"] for tag in response.json().get("results", [])]}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/exists")
def check_image(
    image: str = Query(..., description="The name of the Docker image to check"),
    env_manager=Depends(get_env_manager),
):
    """
    Check if a Docker image exists locally.
    """
    try:
        # Using the docker interface from EnvironmentManager
        env_manager.docker_iface.get_image(image)
        return {"status": "found"}
    except DockerInterfaceImageNotFoundError:
        raise HTTPException(404, "Image not found locally. Ready to pull.")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/pull")
def pull_image(
    image: str = Query(..., description="The name of the Docker image to pull"),
    env_manager=Depends(get_env_manager),
):
    """
    Pull a Docker image and stream the pull progress.
    """

    def image_pull_stream():
        layers = {}
        total_download_size = 0
        total_downloaded = 0
        try:
            for line in env_manager.docker_iface.pull_image_api(image):
                status = line.get("status")
                layer_id = line.get("id")
                progress_detail = line.get("progressDetail", {})

                if layer_id:
                    if status == "Pull complete":
                        pass  # layer is done
                    elif status == "Already exists":
                        pass
                    elif "current" in progress_detail and "total" in progress_detail:
                        current = progress_detail.get("current", 0)
                        total = progress_detail.get("total", 0)
                        if total > 0:
                            if layer_id not in layers:
                                layers[layer_id] = {"current": current, "total": total}
                                total_download_size += total
                                total_downloaded += current
                            else:
                                total_downloaded -= layers[layer_id]["current"]
                                layers[layer_id]["current"] = current
                                total_downloaded += current

                        overall_progress = (
                            (total_downloaded / total_download_size) * 100
                            if total_download_size > 0
                            else 0
                        )
                        yield f"data: {json.dumps({'progress': overall_progress})}\n\n"

            yield f"data: {json.dumps({'progress': 100, 'status': 'completed'})}\n\n"
        except DockerInterfaceError as e:
            yield f"data: {json.dumps({'error': f'Error pulling image {image}: {e}'})}\n\n"

    return StreamingResponse(image_pull_stream(), media_type="text/event-stream")
