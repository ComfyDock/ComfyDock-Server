from comfydock_core.docker_interface import DockerInterface, DockerInterfaceContainerNotFoundError
from .config import ServerConfig
from comfydock_core.logging import get_logger
import logging

class DockerManager:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.docker_interface = DockerInterface()

    @staticmethod
    def set_docker_interface_log_level(level: int | str):
        """
        Set the logging level for the DockerInterface logger.
        
        Args:
            level: Logging level (e.g., logging.INFO, 'INFO', logging.DEBUG, 'DEBUG')
        """
        docker_interface_logger = get_logger('comfydock_core.docker_interface')
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        docker_interface_logger.setLevel(level)

    def start_frontend(self):
        """Start the frontend container using core DockerInterface"""
        image_name = f"{self.config.frontend_image}:{self.config.frontend_version}"
        
        # First check if the image exists, if not, pull it
        self.docker_interface.try_pull_image(image_name)
        
        try:
            # Use core library's container retrieval
            container = self.docker_interface.get_container(self.config.frontend_container_name)
            
            # Use core library's status check and start mechanism
            if container.status != 'running':
                self.docker_interface.start_container(container)
                
        except DockerInterfaceContainerNotFoundError:
            # Use core library's container run method
            self.docker_interface.run_container(
                image=image_name,
                name=self.config.frontend_container_name,
                ports={f'{self.config.frontend_container_port}/tcp': self.config.frontend_host_port},
                detach=True,
                remove=True
            )

    def stop_frontend(self):
        """Stop the frontend container using core DockerInterface"""
        try:
            container = self.docker_interface.get_container(self.config.frontend_container_name)
            self.docker_interface.stop_container(container)
        except DockerInterfaceContainerNotFoundError:
            pass