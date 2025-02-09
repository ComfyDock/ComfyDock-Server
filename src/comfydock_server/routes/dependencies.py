from fastapi import Request, Depends, HTTPException
from ..config import ServerConfig

def get_env_manager(request: Request):
    return request.app.state.env_manager

def get_user_settings_manager(request: Request):
    return request.app.state.user_settings_manager

def get_connection_manager(request: Request):
    return request.app.state.connection_manager
  
def get_config(request: Request) -> ServerConfig:
    return request.app.state.config