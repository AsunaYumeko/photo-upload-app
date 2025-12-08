"""Config Storage module for Photo Upload App.

This module handles configuration persistence using JSON files.
"""

import json
import os
import re
from typing import Optional

from src.models import AppConfig


class ConfigStorage:
    """配置存储 - Handles loading and saving application configuration."""
    
    def __init__(self, config_path: str):
        """初始化，设置配置文件路径
        
        Args:
            config_path: Path to the configuration JSON file.
        """
        self._config_path = config_path
    
    def load(self) -> AppConfig:
        """加载配置
        
        Returns:
            AppConfig: Loaded configuration, or default if file doesn't exist.
        """
        if not os.path.exists(self._config_path):
            return AppConfig()
        
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppConfig.from_dict(data)
        except (json.JSONDecodeError, IOError):
            return AppConfig()
    
    def save(self, config: AppConfig) -> bool:
        """保存配置
        
        Args:
            config: Configuration to save.
            
        Returns:
            bool: True if save was successful, False otherwise.
        """
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(self._config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError):
            return False
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证 URL 格式
        
        Validates that the URL conforms to HTTP/HTTPS format with
        scheme, host, optional port and path.
        
        Args:
            url: URL string to validate.
            
        Returns:
            bool: True if URL is valid HTTP/HTTPS format.
        """
        if not url or not isinstance(url, str):
            return False
        
        # Pattern for HTTP/HTTPS URLs
        # Matches: scheme://host[:port][/path]
        pattern = r'^https?://[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*(\:[0-9]+)?(/.*)?$'
        
        return bool(re.match(pattern, url))
