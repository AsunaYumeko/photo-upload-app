"""Camera Module for Photo Upload App.

This module handles camera operations using Plyer library.
"""

import os
from typing import Callable, Optional
from datetime import datetime
from kivy.clock import Clock

# Check if running on Android
try:
    from android import mActivity
    from android.permissions import request_permissions, check_permission, Permission
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False

# Import plyer camera
try:
    from plyer import camera
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    camera = None


class CameraModule:
    """Camera module - Handles camera capture operations."""
    
    def __init__(self, save_path: str):
        """Initialize with photo save path."""
        self._save_path = save_path
        self._pending_callback = None
        self._pending_filepath = None
        self._ensure_save_path_exists()
    
    def _ensure_save_path_exists(self) -> None:
        """Ensure the save directory exists."""
        if self._save_path:
            try:
                if not os.path.exists(self._save_path):
                    os.makedirs(self._save_path)
            except Exception as e:
                print(f"Failed to create save path: {e}")
                # Try alternative path on Android
                if ANDROID_AVAILABLE:
                    self._save_path = self._get_android_pictures_path()
    
    def _get_android_pictures_path(self) -> str:
        """Get Android pictures directory."""
        if ANDROID_AVAILABLE:
            try:
                from jnius import autoclass
                Environment = autoclass('android.os.Environment')
                pictures_dir = Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_PICTURES
                ).getAbsolutePath()
                app_dir = os.path.join(pictures_dir, 'PhotoUpload')
                if not os.path.exists(app_dir):
                    os.makedirs(app_dir)
                return app_dir
            except Exception as e:
                print(f"Failed to get Android pictures path: {e}")
        return self._save_path
    
    def _generate_filename(self) -> str:
        """Generate a unique filename based on timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"photo_{timestamp}.jpg"
    
    def capture(self, callback: Callable[[Optional[str]], None]) -> None:
        """Capture photo and return path via callback."""
        if not self.is_available():
            print("Camera not available")
            callback(None)
            return
        
        # Request permissions first on Android
        if ANDROID_AVAILABLE:
            self._request_permissions_and_capture(callback)
        else:
            self._do_capture(callback)
    
    def _request_permissions_and_capture(self, callback: Callable) -> None:
        """Request camera permissions then capture."""
        def on_permissions(permissions, grants):
            if all(grants):
                # Schedule capture on main thread
                Clock.schedule_once(lambda dt: self._do_capture(callback), 0.1)
            else:
                print("Camera permission denied")
                callback(None)
        
        try:
            request_permissions(
                [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE],
                on_permissions
            )
        except Exception as e:
            print(f"Permission request error: {e}")
            # Try capture anyway
            self._do_capture(callback)
    
    def _do_capture(self, callback: Callable) -> None:
        """Perform the actual capture."""
        filename = self._generate_filename()
        filepath = os.path.join(self._save_path, filename)
        
        self._pending_callback = callback
        self._pending_filepath = filepath
        
        print(f"Capturing to: {filepath}")
        
        try:
            camera.take_picture(
                filename=filepath,
                on_complete=self._on_capture_complete
            )
        except Exception as e:
            print(f"Camera capture error: {e}")
            callback(None)
    
    def _on_capture_complete(self, path: Optional[str]) -> None:
        """Handle camera capture completion."""
        callback = self._pending_callback
        filepath = self._pending_filepath
        
        print(f"Capture complete, path: {path}, expected: {filepath}")
        
        if callback:
            # Use returned path if available, otherwise use our filepath
            result_path = path if path else filepath
            
            # Verify file exists
            if result_path and os.path.exists(result_path):
                print(f"Photo saved: {result_path}")
                callback(result_path)
            elif filepath and os.path.exists(filepath):
                print(f"Using expected path: {filepath}")
                callback(filepath)
            else:
                print("Photo file not found")
                callback(None)
            
            # Clear pending
            self._pending_callback = None
            self._pending_filepath = None
    
    def is_available(self) -> bool:
        """Check if camera is available."""
        if not PLYER_AVAILABLE or camera is None:
            return False
        
        try:
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
