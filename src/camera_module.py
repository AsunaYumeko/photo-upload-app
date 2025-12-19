"""Camera Module for Photo Upload App.

Uses Android camera Intent with thumbnail mode.
"""

import os
from typing import Callable, Optional
from datetime import datetime
from kivy.clock import Clock

# Check if running on Android
ANDROID_AVAILABLE = False
try:
    from jnius import autoclass, cast
    from android import activity, mActivity
    
    # Java classes
    Intent = autoclass('android.content.Intent')
    MediaStore = autoclass('android.provider.MediaStore')
    Environment = autoclass('android.os.Environment')
    Bitmap = autoclass('android.graphics.Bitmap')
    FileOutputStream = autoclass('java.io.FileOutputStream')
    CompressFormat = autoclass('android.graphics.Bitmap$CompressFormat')
    
    ANDROID_AVAILABLE = True
except ImportError as e:
    pass
except Exception as e:
    pass

# Fallback for desktop
PLYER_AVAILABLE = False
try:
    from plyer import camera as plyer_camera
    PLYER_AVAILABLE = True
except ImportError:
    pass


REQUEST_CODE_CAMERA = 1001


class CameraModule:
    """Camera module using Android camera Intent."""
    
    _callback = None
    _filepath = None
    _bound = False
    _last_error = ""
    
    def __init__(self, save_path: str):
        """Initialize with photo save path."""
        self._save_path = save_path
        self._ensure_save_path_exists()
        
        # Bind activity result handler once
        if ANDROID_AVAILABLE and not CameraModule._bound:
            try:
                activity.bind(on_activity_result=CameraModule._on_activity_result)
                CameraModule._bound = True
            except Exception as e:
                CameraModule._last_error = f"Bind error: {e}"
    
    def _ensure_save_path_exists(self) -> None:
        """Ensure the save directory exists."""
        if self._save_path:
            try:
                if not os.path.exists(self._save_path):
                    os.makedirs(self._save_path)
            except Exception:
                pass
    
    def _generate_filename(self) -> str:
        """Generate a unique filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"photo_{timestamp}.jpg"
    
    def capture(self, callback: Callable[[Optional[str]], None]) -> None:
        """Capture photo."""
        CameraModule._last_error = ""
        
        if ANDROID_AVAILABLE:
            self._capture_android(callback)
        elif PLYER_AVAILABLE:
            self._capture_plyer(callback)
        else:
            CameraModule._last_error = "No camera module"
            callback(None)
    
    def _capture_android(self, callback: Callable) -> None:
        """Capture using Android camera Intent."""
        try:
            filename = self._generate_filename()
            
            # Get save directory
            context = mActivity.getApplicationContext()
            files_dir = context.getExternalFilesDir(Environment.DIRECTORY_PICTURES)
            
            if files_dir is None:
                files_dir = context.getExternalCacheDir()
            
            if files_dir is None:
                CameraModule._last_error = "No storage"
                callback(None)
                return
            
            filepath = os.path.join(files_dir.getAbsolutePath(), filename)
            
            # Store for callback
            CameraModule._callback = callback
            CameraModule._filepath = filepath
            
            # Create camera intent - thumbnail mode (no EXTRA_OUTPUT)
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            
            # Check if camera app exists
            pm = context.getPackageManager()
            if intent.resolveActivity(pm) is None:
                CameraModule._last_error = "No camera app"
                callback(None)
                return
            
            # Start camera activity
            mActivity.startActivityForResult(intent, REQUEST_CODE_CAMERA)
            
        except Exception as e:
            CameraModule._last_error = f"Launch error: {e}"
            callback(None)
    
    def _capture_plyer(self, callback: Callable) -> None:
        """Capture using plyer (desktop fallback)."""
        try:
            filename = self._generate_filename()
            filepath = os.path.join(self._save_path, filename)
            plyer_camera.take_picture(
                filename=filepath,
                on_complete=lambda p: callback(p if p else filepath)
            )
        except Exception as e:
            CameraModule._last_error = str(e)
            callback(None)
    
    @staticmethod
    def _on_activity_result(request_code, result_code, intent):
        """Handle camera result."""
        if request_code != REQUEST_CODE_CAMERA:
            return
        
        callback = CameraModule._callback
        filepath = CameraModule._filepath
        
        # Clear
        CameraModule._callback = None
        CameraModule._filepath = None
        
        if callback is None:
            return
        
        # -1 = RESULT_OK
        if result_code == -1 and intent is not None:
            try:
                # Get thumbnail bitmap from intent extras
                extras = intent.getExtras()
                if extras is None:
                    CameraModule._last_error = "No extras"
                    Clock.schedule_once(lambda dt: callback(None), 0)
                    return
                
                if not extras.containsKey("data"):
                    CameraModule._last_error = "No data key"
                    Clock.schedule_once(lambda dt: callback(None), 0)
                    return
                
                # Method 1: Try direct getParcelable with Bitmap class
                try:
                    bitmap = extras.getParcelable("data")
                    if bitmap is not None:
                        # bitmap is already a Bitmap object
                        fos = FileOutputStream(filepath)
                        bitmap.compress(CompressFormat.JPEG, 90, fos)
                        fos.flush()
                        fos.close()
                        
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            Clock.schedule_once(lambda dt, p=filepath: callback(p), 0)
                            return
                except Exception as e1:
                    CameraModule._last_error = f"Method1: {e1}"
                
                # Method 2: Try get() and cast
                try:
                    obj = extras.get("data")
                    if obj is not None:
                        bitmap = cast('android.graphics.Bitmap', obj)
                        fos = FileOutputStream(filepath)
                        bitmap.compress(CompressFormat.JPEG, 90, fos)
                        fos.flush()
                        fos.close()
                        
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            Clock.schedule_once(lambda dt, p=filepath: callback(p), 0)
                            return
                except Exception as e2:
                    CameraModule._last_error = f"Method2: {e2}"
                
                CameraModule._last_error = "Failed to get bitmap"
                
            except Exception as e:
                CameraModule._last_error = f"Result error: {e}"
        elif result_code == 0:
            CameraModule._last_error = "Cancelled"
        else:
            CameraModule._last_error = f"Code: {result_code}"
        
        Clock.schedule_once(lambda dt: callback(None), 0)
    
    def is_available(self) -> bool:
        """Check if camera is available."""
        return ANDROID_AVAILABLE or PLYER_AVAILABLE
    
    def get_last_error(self) -> str:
        """Get last error message."""
        return CameraModule._last_error
    
    @property
    def save_path(self) -> str:
        return self._save_path
    
    @save_path.setter
    def save_path(self, path: str) -> None:
        self._save_path = path
        self._ensure_save_path_exists()
