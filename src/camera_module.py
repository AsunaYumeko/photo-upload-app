"""Camera Module for Photo Upload App.

This module handles camera operations using Plyer library.
"""

import os
from typing import Callable, Optional
from datetime import datetime

try:
    from plyer import camera
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class CameraModule:
    """摄像头模块 - Handles camera capture operations."""
    
    def __init__(self, save_path: str):
        """初始化，设置照片保存路径
        
        Args:
            save_path: Directory path where photos will be saved.
        """
        self._save_path = save_path
        self._ensure_save_path_exists()
    
    def _ensure_save_path_exists(self) -> None:
        """Ensure the save directory exists."""
        if self._save_path and not os.path.exists(self._save_path):
            os.makedirs(self._save_path)
    
    def _generate_filename(self) -> str:
        """Generate a unique filename based on timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"photo_{timestamp}.jpg"
    
    def capture(self, callback: Callable[[Optional[str]], None]) -> None:
        """拍照并通过回调返回照片路径
        
        Args:
            callback: Callback function that receives the photo path on success,
                     or None on failure.
        """
        if not self.is_available():
            callback(None)
            return
        
        filename = self._generate_filename()
        filepath = os.path.join(self._save_path, filename)
        
        try:
            camera.take_picture(
                filename=filepath,
                on_complete=lambda path: callback(path if path else filepath)
            )
        except Exception:
            callback(None)
    
    def is_available(self) -> bool:
        """检查摄像头是否可用
        
        Returns:
            bool: True if camera is available, False otherwise.
        """
        if not PLYER_AVAILABLE:
            return False
        
        try:
            # Check if camera exists (platform-dependent)
            return hasattr(camera, 'take_picture')
        except Exception:
            return False
    
    @property
    def save_path(self) -> str:
        """Get current save path."""
        return self._save_path
    
    @save_path.setter
    def save_path(self, path: str) -> None:
        """Set save path and ensure it exists."""
        self._save_path = path
        self._ensure_save_path_exists()
