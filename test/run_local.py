from comfydock_server.config import ServerConfig
from comfydock_server.server import ComfyDockServer


def run():
    # Create test configuration
    config = ServerConfig(
        comfyui_path="./ComfyUI",
        db_file_path="./environments.json",
        user_settings_file_path="./user.settings.json",
        frontend_image="comfydock-frontend",
        frontend_version="0.1.1",
        frontend_port=8000,
        backend_port=5172,
        backend_host="127.0.0.1",
        allow_multiple_containers=False,
    )

    # Initialize server
    server = ComfyDockServer(config)

    try:
        print("Starting server...")
        server.start()

        # Keep server running for manual testing
        input("Press Enter to stop server...")

    finally:
        print("Stopping server...")
        server.stop()


if __name__ == "__main__":
    run()
