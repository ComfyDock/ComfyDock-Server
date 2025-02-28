import logging
from comfydock_server.config import ServerConfig
from comfydock_server.server import ComfyDockServer


def configure_logging():
    """Configure logging for local development."""
    # Create logger
    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)
    
    # Create console handler and set level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add formatter to handler
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


def run():
    # Configure logging
    logger = configure_logging()
    logger.info("Starting ComfyDock server in local development mode")
    
    # Create test configuration
    config = ServerConfig(
        comfyui_path="./ComfyUI",
        db_file_path="./environments.json",
        user_settings_file_path="./user.settings.json",
        backend_port=5172,
        backend_host="127.0.0.1",
        allow_multiple_containers=False,
        dockerhub_tags_url="https://hub.docker.com/v2/repositories/akatzai/comfydock-env/tags",
    )

    # Initialize server
    server = ComfyDockServer(config)

    try:
        logger.info("Starting server...")
        print("Starting server...")
        server.start_backend()

        # Keep server running for manual testing
        input("Press Enter to stop server...")

    finally:
        logger.info("Stopping server...")
        print("Stopping server...")
        server.stop()


if __name__ == "__main__":
    run()
