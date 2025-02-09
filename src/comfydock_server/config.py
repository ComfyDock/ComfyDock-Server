from pydantic_settings import BaseSettings

class ServerConfig(BaseSettings):
    comfyui_path: str = "./ComfyUI"
    db_file_path: str = "environments.json"
    user_settings_file_path: str = "user_settings.json"
    frontend_image: str = "akatzai/comfy-env-frontend"
    frontend_version: str = "0.5.1"
    backend_host: str = "127.0.0.1"
    backend_port: int = 5172
    frontend_port: int = 8000
    allow_multiple_containers: bool = False
    dockerhub_images_url: str = "https://hub.docker.com/v2/namespaces/akatzai/repositories/comfyui-env/tags?page_size=100"

    class Config:
        env_prefix = "COMFYDOCK_"