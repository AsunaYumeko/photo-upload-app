"""Main application module for Photo Upload App.

This is the entry point for the Kivy application.
"""

import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.lang import Builder

from src.camera_module import CameraModule
from src.image_converter import ImageConverter
from src.upload_service import UploadService
from src.config_storage import ConfigStorage
from src.permission_manager import PermissionManager
from src.models import AppConfig, PhotoData


# Get the directory where this file is located
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
PHOTOS_DIR = os.path.join(APP_DIR, "photos")

# Load the KV file
Builder.load_file(os.path.join(APP_DIR, "photoupload.kv"))


class MainScreen(Screen):
    """主屏幕，包含拍照和上传功能"""
    
    current_photo_path = StringProperty("")
    current_base64 = StringProperty("")
    is_uploading = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._camera = CameraModule(PHOTOS_DIR)
        self._upload_service = None
        self._config_storage = ConfigStorage(CONFIG_PATH)
    
    def on_enter(self):
        """Called when screen is displayed."""
        self._load_config()
    
    def _load_config(self):
        """Load configuration and initialize upload service."""
        config = self._config_storage.load()
        if config.api_url:
            self._upload_service = UploadService(config.api_url)
    
    def capture_photo(self):
        """触发拍照"""
        if not self._camera.is_available():
            self.show_notification("摄像头不可用，请检查权限设置", is_error=True)
            return
        
        self.show_notification("正在打开摄像头...")
        self._camera.capture(self._on_photo_captured)
    
    def _on_photo_captured(self, photo_path):
        """Callback when photo is captured."""
        if not photo_path:
            self.show_notification("拍照失败，请重试", is_error=True)
            return
        
        self.current_photo_path = photo_path
        self.show_preview(photo_path)
        
        # Convert to Base64
        result = ImageConverter.encode_to_base64(photo_path)
        if result.success:
            self.current_base64 = result.value
            self.ids.upload_btn.disabled = False
            self.show_notification("照片已准备好上传")
        else:
            self.show_notification(f"图片处理失败: {result.value}", is_error=True)
    
    def upload_photo(self):
        """触发上传"""
        if not self.current_base64:
            self.show_notification("请先拍照", is_error=True)
            return
        
        if not self._upload_service:
            self.show_notification("请先配置 API 地址", is_error=True)
            return
        
        self.is_uploading = True
        self._show_loading(True)
        self.show_notification("正在上传...")
        
        # Run upload in background
        Clock.schedule_once(lambda dt: self._do_upload(), 0.1)
    
    def _do_upload(self):
        """Perform the actual upload."""
        filename = os.path.basename(self.current_photo_path) if self.current_photo_path else "photo.jpg"
        result = self._upload_service.upload_image(self.current_base64, filename)
        
        self.is_uploading = False
        self._show_loading(False)
        
        if result.success:
            self.show_notification("上传成功！", is_error=False)
            # Reset state after successful upload
            self.current_photo_path = ""
            self.current_base64 = ""
            self.ids.upload_btn.disabled = True
            self.ids.photo_preview.source = ""
            self.ids.preview_placeholder.opacity = 1
        else:
            self.show_notification(result.message, is_error=True)
    
    def show_preview(self, image_path: str):
        """显示照片预览"""
        self.ids.photo_preview.source = image_path
        self.ids.preview_placeholder.opacity = 0
    
    def show_notification(self, message: str, is_error: bool = False):
        """显示通知消息"""
        self.ids.status_label.text = message
        self.ids.status_label.color = (1, 0, 0, 1) if is_error else (0, 0.5, 0, 1)
    
    def _show_loading(self, show: bool):
        """Show or hide loading indicator."""
        self.ids.loading_bar.opacity = 1 if show else 0
        self.ids.loading_bar.value = 50 if show else 0
        self.ids.capture_btn.disabled = show
        self.ids.upload_btn.disabled = show


class SettingsScreen(Screen):
    """设置屏幕，配置 API 端点"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config_storage = ConfigStorage(CONFIG_PATH)
    
    def on_enter(self):
        """Called when screen is displayed."""
        self.load_config()
    
    def load_config(self):
        """加载当前配置"""
        config = self._config_storage.load()
        self.ids.api_url_input.text = config.api_url
        self.ids.validation_label.text = ""
    
    def save_config(self):
        """保存配置"""
        api_url = self.ids.api_url_input.text.strip()
        
        # Validate URL if not empty
        if api_url and not ConfigStorage.validate_url(api_url):
            self.ids.validation_label.text = "API 地址格式无效"
            return False
        
        config = AppConfig(api_url=api_url)
        if self._config_storage.save(config):
            self.ids.validation_label.text = ""
            self.ids.validation_label.color = (0, 0.5, 0, 1)
            self.ids.validation_label.text = "保存成功"
            return True
        else:
            self.ids.validation_label.text = "保存失败"
            return False


class PhotoUploadApp(App):
    """主应用类"""
    
    def build(self):
        """构建应用 UI"""
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm
    
    def on_start(self):
        """应用启动时请求权限"""
        PermissionManager.request_all_permissions(self._on_permissions_result)
    
    def _on_permissions_result(self, granted: bool):
        """Handle permission request result."""
        if not granted:
            # Show message about permissions
            main_screen = self.root.get_screen('main')
            main_screen.show_notification(
                "需要摄像头和存储权限才能使用此应用",
                is_error=True
            )


def main():
    """Application entry point."""
    PhotoUploadApp().run()


if __name__ == '__main__':
    main()
