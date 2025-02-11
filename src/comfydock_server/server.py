from pathlib import Path
import subprocess
import signal
import sys
from typing import Optional
from .docker_utils import DockerManager
from .config import ServerConfig
import uvicorn
import threading
from .app import create_app
import logging
import logging.handlers


class ComfyDockServer:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.server = None
        self.server_thread = None
        self.docker = DockerManager(config)
        self.running = False
        
    def set_log_level(self, level: int | str = logging.INFO):
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s %(name)s [%(levelname)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S %z"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "detailed",
                    "level": "INFO"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "detailed",
                    "filename": "comfydock.log",
                    "mode": "a",
                    "maxBytes": 10485760,
                    "backupCount": 3,
                    "level": "INFO"
                }
            },
            "loggers": {
                "": {  # root logger
                    "handlers": ["console", "file"],
                    "level": "INFO",
                },
                "comfydock_core": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False
                },
            }
        })

    def start(self):
        """Start both backend server and frontend container"""
        self.docker.start_frontend()
        self.start_backend()
        self.running = True
        self._register_signal_handlers()

    def stop(self):
        """Stop both components"""
        self.stop_backend()
        self.docker.stop_frontend()
        self.running = False

    def start_backend(self):
        """Start the FastAPI server using uvicorn programmatically"""
        config = uvicorn.Config(
            app=create_app(self.config),
            host=self.config.backend_host,
            port=self.config.backend_port,
            log_config=None
        )
        self.server = uvicorn.Server(config)
        
        # Run server in a separate thread since server.run() is blocking
        self.server_thread = threading.Thread(target=self.server.run)
        self.server_thread.start()

    def stop_backend(self):
        """Stop the backend server"""
        if self.server:
            self.server.should_exit = True
            if self.server_thread:
                self.server_thread.join()

    def _register_signal_handlers(self):
        """Handle graceful shutdown on SIGINT/SIGTERM"""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Signal handler for shutdown"""
        self.stop()
        sys.exit(0)