"""Permission Manager module for Photo Upload App.

This module handles Android permission requests using Plyer library.
"""

from typing import Callable

try:
    from android.permissions import request_permissions, check_permission, Permission
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False


class PermissionManager:
    """权限管理器 - Handles Android permission requests."""
    
    # Permission constants
    CAMERA = "android.permission.CAMERA"
    WRITE_STORAGE = "android.permission.WRITE_EXTERNAL_STORAGE"
    READ_STORAGE = "android.permission.READ_EXTERNAL_STORAGE"
    
    @staticmethod
    def request_camera_permission(callback: Callable[[bool], None]) -> None:
        """请求摄像头权限
        
        Args:
            callback: Callback function that receives True if permission granted.
        """
        if not ANDROID_AVAILABLE:
            # On non-Android platforms, assume permission granted
            callback(True)
            return
        
        def on_permissions_result(permissions, grants):
            granted = all(grants)
            callback(granted)
        
        try:
            request_permissions(
                [Permission.CAMERA],
                on_permissions_result
            )
        except Exception:
            callback(False)
    
    @staticmethod
    def request_storage_permission(callback: Callable[[bool], None]) -> None:
        """请求存储权限
        
        Args:
            callback: Callback function that receives True if permission granted.
        """
        if not ANDROID_AVAILABLE:
            # On non-Android platforms, assume permission granted
            callback(True)
            return
        
        def on_permissions_result(permissions, grants):
            granted = all(grants)
            callback(granted)
        
        try:
            request_permissions(
                [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE],
                on_permissions_result
            )
        except Exception:
            callback(False)
    
    @staticmethod
    def request_all_permissions(callback: Callable[[bool], None]) -> None:
        """请求所有必要权限（摄像头和存储）
        
        Args:
            callback: Callback function that receives True if all permissions granted.
        """
        if not ANDROID_AVAILABLE:
            callback(True)
            return
        
        def on_permissions_result(permissions, grants):
            granted = all(grants)
            callback(granted)
        
        try:
            request_permissions(
                [
                    Permission.CAMERA,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE
                ],
                on_permissions_result
            )
        except Exception:
            callback(False)
    
    @staticmethod
    def check_camera_permission() -> bool:
        """检查摄像头权限
        
        Returns:
            bool: True if camera permission is granted.
        """
        if not ANDROID_AVAILABLE:
            return True
        
        try:
            return check_permission(Permission.CAMERA)
        except Exception:
            return False
    
    @staticmethod
    def check_storage_permission() -> bool:
        """检查存储权限
        
        Returns:
            bool: True if storage permission is granted.
        """
        if not ANDROID_AVAILABLE:
            return True
        
        try:
            return (
                check_permission(Permission.WRITE_EXTERNAL_STORAGE) and
                check_permission(Permission.READ_EXTERNAL_STORAGE)
            )
        except Exception:
            return False
