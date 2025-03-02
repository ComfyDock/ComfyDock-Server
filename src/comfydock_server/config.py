from pydantic_settings import BaseSettings

class ServerConfig(BaseSettings):
    comfyui_path: str = "./ComfyUI"
    db_file_path: str = "environments.json"
    user_settings_file_path: str = "user.settings.json"
    frontend_container_name: str = "comfydock-frontend"
    frontend_image: str = "akatzai/comfydock-frontend:latest"
    backend_host: str = "localhost"
    backend_port: int = 5172
    frontend_container_port: int = 8000
    frontend_host_port: int = 8000
    allow_multiple_containers: bool = False
    dockerhub_tags_url: str = "https://hub.docker.com/v2/namespaces/akatzai/repositories/comfydock-env/tags?page_size=100"

    class Config:
        env_prefix = "COMFYDOCK_"