"""Main application module for Photo Upload App.

This is the entry point for the Kivy application.
"""

import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.clock import Clock
from kivy.lang import Builder
from camera_module import CameraModule
from image_converter import ImageConverter
from upload_service import UploadService
from config_storage import ConfigStorage
from permission_manager import PermissionManager
from models import AppConfig, PhotoData


# Get the directory where this file is located
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

# Use app private directory for photos (works on Android)
def get_photos_dir():
    """Get photos directory that works on Android."""
    try:
        from android import mActivity
        # Use app's external files directory on Android
        context = mActivity.getApplicationContext()
        files_dir = context.getExternalFilesDir(None)
        if files_dir:
            photos_dir = os.path.join(files_dir.getAbsolutePath(), 'photos')
        else:
            photos_dir = os.path.join(APP_DIR, "photos")
    except ImportError:
        # Not on Android, use local directory
        photos_dir = os.path.join(APP_DIR, "photos")
    
    if not os.path.exists(photos_dir):
        try:
            os.makedirs(photos_dir)
        except Exception:
            pass
    return photos_dir

PHOTOS_DIR = get_photos_dir()

# Load the KV file
Builder.load_file(os.path.join(APP_DIR, "photoupload.kv"))


class MainScreen(Screen):
    """Main screen with task list and photo capture"""
    
    current_photo_path = StringProperty("")
    current_base64 = StringProperty("")
    current_order_no = StringProperty("")
    is_uploading = BooleanProperty(False)
    image_urls = ListProperty([])  # Store converted image URLs
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._camera = CameraModule(PHOTOS_DIR)
        self._upload_service = None
        self._config_storage = ConfigStorage(CONFIG_PATH)
        self._tasks = []
    
    def on_enter(self):
        """Called when screen is displayed."""
        self._load_config()
    
    def _load_config(self):
        """Load configuration and initialize upload service."""
        config = self._config_storage.load()
        if config.api_url:
            self._upload_service = UploadService(config.api_url)
    
    def refresh_tasks(self):
        """Refresh task list from server"""
        if not self._upload_service:
            self.show_notification("Configure API first", is_error=True)
            return
        
        self.show_notification("Loading tasks...")
        Clock.schedule_once(lambda dt: self._do_refresh_tasks(), 0.1)
    
    def _do_refresh_tasks(self):
        """Perform task refresh"""
        result = self._upload_service.get_tasks()
        if result.success:
            self._tasks = result.response_data.get("tasks", [])
            self._update_task_list()
            self.show_notification(f"Loaded {len(self._tasks)} tasks")
        else:
            self.show_notification(result.message, is_error=True)
    
    def _update_task_list(self):
        """Update task list UI"""
        task_container = self.ids.task_container
        task_container.clear_widgets()
        
        for task in self._tasks:
            btn = Button(
                text=f"{task.get('orderNo', 'N/A')} - {task.get('lockerNo', '')}",
                size_hint_y=None,
                height=50
            )
            btn.bind(on_release=lambda x, t=task: self.select_task(t))
            task_container.add_widget(btn)
    
    def select_task(self, task):
        """Select a task for processing"""
        self.current_order_no = task.get("orderNo", "")
        self.image_urls = []  # Reset image list
        self.ids.order_label.text = f"Order: {self.current_order_no}"
        self.ids.photo_count_label.text = "Photos: 0"
        self.show_notification(f"Selected: {self.current_order_no}")
        
        # Update status to processing
        if self._upload_service:
            self._upload_service.update_status(self.current_order_no)
    
    def capture_photo(self):
        """Trigger photo capture"""
        if not self.current_order_no:
            self.show_notification("Select task first", is_error=True)
            return
        
        if not self._camera.is_available():
            self.show_notification("Camera unavailable", is_error=True)
            return
        
        self.show_notification("Opening camera...")
        self._camera.capture(self._on_photo_captured)
    
    def _on_photo_captured(self, photo_path):
        """Callback when photo is captured."""
        if not photo_path:
            self.show_notification("Capture failed", is_error=True)
            return
        
        self.current_photo_path = photo_path
        self.show_preview(photo_path)
        
        # Convert to Base64
        result = ImageConverter.encode_to_base64(photo_path)
        if result.success:
            self.current_base64 = result.value
            self.show_notification("Converting...")
            # Auto-convert to HTTP URL
            Clock.schedule_once(lambda dt: self._convert_image(), 0.1)
        else:
            self.show_notification(f"Failed: {result.value}", is_error=True)
    
    def _convert_image(self):
        """Convert base64 image to HTTP URL via Swap API"""
        if not self._upload_service:
            self.show_notification("API not configured", is_error=True)
            return
        
        result = self._upload_service.swap_image(self.current_base64)
        if result.success:
            image_url = result.response_data.get("ImageUrl")
            if image_url:
                self.image_urls.append(image_url)
                self.ids.photo_count_label.text = f"Photos: {len(self.image_urls)}"
                self.show_notification(f"Photo {len(self.image_urls)} ready")
        else:
            self.show_notification(result.message, is_error=True)
    
    def submit_sign(self):
        """Submit all photos for sign-off"""
        if not self.current_order_no:
            self.show_notification("Select task first", is_error=True)
            return
        
        if not self.image_urls:
            self.show_notification("Take photo first", is_error=True)
            return
        
        if not self._upload_service:
            self.show_notification("API not configured", is_error=True)
            return
        
        self.is_uploading = True
        self._show_loading(True)
        self.show_notification("Submitting...")
        Clock.schedule_once(lambda dt: self._do_sign(), 0.1)
    
    def _do_sign(self):
        """Perform sign-off"""
        result = self._upload_service.sign_for(self.current_order_no, list(self.image_urls))
        
        self.is_uploading = False
        self._show_loading(False)
        
        if result.success:
            self.show_notification("Success!", is_error=False)
            # Reset state
            self.current_order_no = ""
            self.current_base64 = ""
            self.image_urls = []
            self.ids.order_label.text = "Order: None"
            self.ids.photo_count_label.text = "Photos: 0"
            self.ids.photo_preview.source = ""
            # Refresh task list
            self.refresh_tasks()
        else:
            self.show_notification(result.message, is_error=True)
    
    def show_preview(self, image_path: str):
        """Show photo preview"""
        self.ids.photo_preview.source = image_path
    
    def show_notification(self, message: str, is_error: bool = False):
        """Show notification message"""
        self.ids.status_label.text = message
        self.ids.status_label.color = (1, 0, 0, 1) if is_error else (0, 0.5, 0, 1)
    
    def _show_loading(self, show: bool):
        """Show or hide loading indicator."""
        self.ids.loading_bar.opacity = 1 if show else 0
        self.ids.loading_bar.value = 50 if show else 0


class SettingsScreen(Screen):
    """Settings screen for API configuration"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config_storage = ConfigStorage(CONFIG_PATH)
    
    def on_enter(self):
        """Called when screen is displayed."""
        self.load_config()
    
    def load_config(self):
        """Load current configuration"""
        config = self._config_storage.load()
        self.ids.api_url_input.text = config.api_url
        self.ids.validation_label.text = ""
    
    def save_config(self):
        """Save configuration"""
        api_url = self.ids.api_url_input.text.strip()
        
        if api_url and not ConfigStorage.validate_url(api_url):
            self.ids.validation_label.text = "Invalid URL"
            return False
        
        config = AppConfig(api_url=api_url)
        if self._config_storage.save(config):
            self.ids.validation_label.color = (0, 0.5, 0, 1)
            self.ids.validation_label.text = "Saved"
            return True
        else:
            self.ids.validation_label.text = "Save failed"
            return False
    
    def test_connection(self):
        """Test API connection"""
        api_url = self.ids.api_url_input.text.strip()
        if not api_url:
            self.ids.validation_label.text = "Enter URL"
            return
        
        self.ids.validation_label.text = "Testing..."
        service = UploadService(api_url)
        result = service.ping()
        
        if result.success:
            self.ids.validation_label.color = (0, 0.5, 0, 1)
            self.ids.validation_label.text = "Connected!"
        else:
            self.ids.validation_label.color = (1, 0, 0, 1)
            self.ids.validation_label.text = result.message


class PhotoUploadApp(App):
    """Main application class"""
    
    def build(self):
        """Build application UI"""
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm
    
    def on_start(self):
        """Request permissions on app start"""
        PermissionManager.request_all_permissions(self._on_permissions_result)
    
    def _on_permissions_result(self, granted: bool):
        """Handle permission request result."""
        if not granted:
            main_screen = self.root.get_screen('main')
            main_screen.show_notification(
                "Permissions required",
                is_error=True
            )


def main():
    """Application entry point."""
    PhotoUploadApp().run()


if __name__ == '__main__':
    main()
