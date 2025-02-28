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
import logging

# Add this logger at the top of the file with other imports
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/tags")
def get_image_tags(config: ServerConfig = Depends(get_config)):
    """
    Returns a list of Docker image tags along with metadata:
      - tagName
      - fullImageName
      - size
      - lastUpdated
      - digest
    """
    logger.info("Fetching image tags from DockerHub")
    try:
        response = requests.get(config.dockerhub_tags_url)
        data = response.json().get("results", [])

        # Parse the repo name from the DockerHub URL
        # e.g. from https://hub.docker.com/v2/repositories/akatzai/comfydock-env/tags
        # we'll extract akatzai/comfydock-env
        repo_name = config.dockerhub_tags_url.split("/repositories/")[1].split("/tags")[0]

        tags_info = []
        for tag in data:
            tags_info.append({
                "tagName": tag["name"],
                "fullImageName": f"{repo_name}:{tag['name']}",
                "size": tag.get("full_size"),  # in bytes
                "lastUpdated": tag.get("last_updated"),
                "digest": tag.get("digest"),
            })

        logger.info(f"Successfully retrieved {len(tags_info)} tags from DockerHub")
        return {"tags": tags_info}
    except Exception as e:
        logger.error(f"Error fetching image tags: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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


@router.get("/installed")
def get_all_image_tags(env_manager=Depends(get_env_manager)):
    """
    Returns a list of all Docker images installed on the user's machine.
    """
    logger.info("Fetching all local Docker images")
    try:
        images = env_manager.docker_iface.get_all_images()
        
        # Format the response with relevant image details
        images_list = []
        for image in images:
            # Handle multiple tags
            tags = image.tags if hasattr(image, 'tags') and image.tags else ["<none>:<none>"]
            
            # Get image size in bytes
            size_bytes = image.attrs.get('Size', 0) if hasattr(image, 'attrs') else 0
            
            # Get creation date
            created = image.attrs.get('Created', '') if hasattr(image, 'attrs') else ''
            
            # Get image ID (short form)
            image_id = image.short_id if hasattr(image, 'short_id') else image.id
            
            # Get image digest
            repo_digests = image.attrs.get('RepoDigests', []) if hasattr(image, 'attrs') else []
            digest = repo_digests[0].split('@')[1] if repo_digests else None
            
            for tag in tags:
                images_list.append({
                    "id": image_id,
                    "tag": tag,
                    "size": size_bytes,  # size in bytes
                    "created": created,
                    "digest": digest
                })
        
        logger.info(f"Successfully retrieved {len(images_list)} local Docker images")
        return {"images": images_list}
    except DockerInterfaceError as e:
        logger.error(f"Docker interface error when fetching images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error when fetching images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
