from fastapi import APIRouter, Depends, HTTPException
from comfydock_core.user_settings import UserSettings
from .dependencies import get_user_settings_manager, get_env_manager, get_config
from ..config import ServerConfig

router = APIRouter(prefix="/user-settings", tags=["user_settings"])


@router.get("", response_model=UserSettings)
def get_user_settings(user_settings_manager=Depends(get_user_settings_manager)):
    try:
        return user_settings_manager.load()
    except Exception as e:
        raise HTTPException(500, str(e))


@router.put("")
def update_user_settings(
    settings: UserSettings, user_settings_manager=Depends(get_user_settings_manager)
):
    try:
        user_settings_manager.save(settings)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/folders")
def create_folder(
    folder_data: dict,
    user_settings_manager=Depends(get_user_settings_manager),
    config: ServerConfig = Depends(get_config),
):
    """
    Create a new folder. Expects a JSON payload with a "name" key.
    """
    try:
        folder_name = folder_data["name"]
        settings = user_settings_manager.load()
        updated_settings = user_settings_manager.create_folder(settings, folder_name)
        user_settings_manager.save(updated_settings)
        new_folder = next(f for f in updated_settings.folders if f.name == folder_name)
        return {"id": new_folder.id, "name": new_folder.name}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.put("/folders/{folder_id}")
def update_folder(
    folder_id: str,
    folder_data: dict,
    user_settings_manager=Depends(get_user_settings_manager),
    config: ServerConfig = Depends(get_config),
):
    """
    Update a folder's name.
    """
    try:
        new_name = folder_data["name"]
        settings = user_settings_manager.load()
        updated_settings = user_settings_manager.update_folder(
            settings, folder_id, new_name
        )
        user_settings_manager.save(updated_settings)
        updated_folder = next(f for f in updated_settings.folders if f.id == folder_id)
        return {"id": updated_folder.id, "name": updated_folder.name}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        else:
            raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: str,
    user_settings_manager=Depends(get_user_settings_manager),
    env_manager=Depends(get_env_manager),
    config: ServerConfig = Depends(get_config),
):
    """
    Delete a folder. Will fail if any environment is still using this folder.
    """
    try:
        # Check if folder is used by any environments
        envs = env_manager.load_environments()
        for env in envs:
            if folder_id in env.folderIds:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete folder - it contains environments.",
                )

        settings = user_settings_manager.load()
        updated_settings = user_settings_manager.delete_folder(settings, folder_id)
        user_settings_manager.save(updated_settings)
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, str(e))
