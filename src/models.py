"""Data models for Photo Upload App.

This module contains the core data classes used throughout the application.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class AppConfig:
    """应用配置数据模型
    
    Stores the application configuration, primarily the API endpoint URL.
    
    Attributes:
        api_url: The URL of the API endpoint for photo uploads.
    """
    api_url: str = ""
    
    def to_dict(self) -> dict:
        """Convert config to dictionary for serialization."""
        return {"api_url": self.api_url}
    
    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        """Create AppConfig from dictionary.
        
        Args:
            data: Dictionary containing configuration data.
            
        Returns:
            AppConfig instance with values from the dictionary.
        """
        return cls(api_url=data.get("api_url", ""))


@dataclass
class UploadResult:
    """上传结果数据模型
    
    Represents the result of an upload operation.
    
    Attributes:
        success: Whether the upload was successful.
        message: A human-readable message describing the result.
        response_data: Optional dictionary containing the server response.
    """
    success: bool
    message: str
    response_data: Optional[dict] = None


@dataclass
class PhotoData:
    """照片数据模型
    
    Represents photo data including file path and optional Base64 encoding.
    
    Attributes:
        file_path: Path to the photo file on disk.
        base64_data: Optional Base64-encoded representation of the photo.
        timestamp: Optional timestamp when the photo was captured.
    """
    file_path: str
    base64_data: Optional[str] = None
    timestamp: Optional[str] = field(default_factory=lambda: datetime.now().isoformat())
