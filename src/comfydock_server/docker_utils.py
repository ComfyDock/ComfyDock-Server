from comfydock_core.docker_interface import DockerInterface, DockerInterfaceContainerNotFoundError
from .config import ServerConfig

class DockerManager:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.docker_interface = DockerInterface()  # Use core library's interface
        self.frontend_container_name = "comfy-env-frontend"

    def start_frontend(self):
        """Start the frontend container using core DockerInterface"""
        image_name = f"{self.config.frontend_image}:{self.config.frontend_version}"
        
        try:
            # Use core library's container retrieval
            container = self.docker_interface.get_container(self.frontend_container_name)
            
            # Use core library's status check and start mechanism
            if container.status != 'running':
                self.docker_interface.start_container(container)
                
        except DockerInterfaceContainerNotFoundError:
            # Use core library's container run method
            self.docker_interface.run_container(
                image=image_name,
                name=self.frontend_container_name,
                ports={'8000/tcp': self.config.frontend_port},
                detach=True,
                remove=True
            )

    def stop_frontend(self):
        """Stop the frontend container using core DockerInterface"""
        try:
            container = self.docker_interface.get_container(self.frontend_container_name)
            self.docker_interface.stop_container(container)
        except DockerInterfaceContainerNotFoundError:
            pass